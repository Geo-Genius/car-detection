import sys
sys.path.append("..")
import mxnet as mx
import os
from geogeniustools.eolearn.geogenius_areas import PixelRangeSplitter
from geogeniustools.eolearn.geogenius_set import GeogeniusPatchSet
from geogeniustools.images.mosaic_image import MosaicImage
import geojson
MODEL_NAME = "fine_tune"
PARAM_FILENAME = "fine_tune-0000.params"
CHECKPOINT = os.path.join(os.path.abspath(os.path.dirname(__file__)).replace("encoding", "model_file"), "fine_tune")
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)
INPUT_SHAPE = 416
THRESH = 0.4
CLASS_NAMES = [u'car']


def car_detection_process(output_path, cat_ids=None, paths=None, aoi=None):
    print("start check environment variable...")
    obs_env_check()
    print("start load model...")
    model = load_model()
    print("start load data...")
    cat_ids = split2list(cat_ids)
    paths = split2list(paths)
    if aoi is not None:
        aoi = split2list(aoi)
        aoi = [float(i) for i in aoi]
    image_list, patch_set, img_geo_ref = load_data(cat_ids=cat_ids, paths=paths, aoi=aoi)
    print("start predict...")
    response_list = predict_model(model=model, image_list=image_list)
    print("convert to geojson...")
    covert_geojson(patch_set, response_list, output_path, img_geo_ref)
    print("car detection done...")


def load_data(cat_ids, paths, aoi):
    """
    read tiff from OBS and split into GeogeniusPatchSet
    """
    # 读取OBS存储中的影像
    img = MosaicImage(cat_ids=cat_ids, paths=paths)
    img_geo_ref = img.metadata.get("georef")
    # 设置兴趣区
    if aoi is not None and len(aoi) == 4:
        print("start calculate aio...")
        img = img.aoi(bbox=aoi)
    # 设置影像划分策略，当前模型输入h、w为416*416，因此，INPUT_SHAPE值设为416
    bbox_splitter = PixelRangeSplitter(img.shape[1:], (INPUT_SHAPE, INPUT_SHAPE), (INPUT_SHAPE, INPUT_SHAPE))
    # 将影像依照划分策略划分，组成划分数据集GeogeniusPatchSet
    patch_set = GeogeniusPatchSet(img[0:3, :, :], bbox_splitter)
    # 将划分数据集组装成网络输入需要格式的array
    image_list = get_image_array(patch_set)
    return image_list, patch_set, img_geo_ref


def get_image_array(patch_set):
    """
    get image array from GeogeniusPatchSet
    """
    data_shapes = [('data', (1, 3, INPUT_SHAPE, INPUT_SHAPE))]
    image_list = []
    shape = patch_set.shape
    try:
        for h in range(shape[0]):
            for w in range(shape[1]):
                img_arr = mx.nd.array(patch_set.patch_index[h][w].data['BANDS'].squeeze())
                img_arr = mx.nd.image.to_tensor(img_arr)
                img_arr = mx.nd.image.normalize(img_arr, mean=MEAN, std=STD)
                batch_data = mx.io.DataBatch(data=[mx.nd.stack(img_arr)],
                                             provide_data=data_shapes)
                image_list.append(batch_data)
    except Exception as e:
        print("error when split patch to batch: ", e)
        sys.stderr.write(e)
        exit(1)
    return image_list


def load_model():
    # GPU环境
    # try:
    #     _ = mx.nd.array([], ctx=mx.gpu())
    #     ctx = mx.gpu()
    #     print("set context to gpu")
    # except mx.MXNetError:
    #     ctx = mx.cpu()
    #     print("set context to cpu")
    # CPU环境
    ctx = mx.cpu()
    data_shapes = [('data', (1, 3, INPUT_SHAPE, INPUT_SHAPE))]
    epoch = 0
    try:
        epoch = int(PARAM_FILENAME[len(MODEL_NAME) + 1:-len('.params')])
    except Exception as e:
        print("error when load model file: ", e)
        sys.stderr.write("Failed to parse epoch from param file, setting epoch to 0")
        exit(1)
    sym, arg_params, aux_params = mx.model.load_checkpoint(CHECKPOINT, epoch)
    mx_model = mx.mod.Module(
        context=ctx,
        symbol=sym,
        data_names=['data'],
        label_names=None)
    mx_model.bind(
        for_training=False,
        data_shapes=data_shapes,
        label_shapes=None)
    mx_model.set_params(arg_params, aux_params, allow_missing=True)
    return mx_model


def predict_model(model, image_list):
    response_list = []
    try:
        for image in image_list:
            model.forward(image)
            pred = model.get_outputs()
            ids, scores, bboxes = [xx[0].asnumpy() for xx in pred]
            response = {
                'detection_classes': [],
                'detection_boxes': [],
                'detection_scores': []
            }
            for idx in range(ids.shape[0]):
                if ids[idx][0] < 0 or scores[idx][0] < THRESH:
                    continue
                response['detection_classes'].append(
                    str(CLASS_NAMES[int(ids[idx][0])].encode('utf-8')))
                response['detection_boxes'].append([
                    (int(bboxes[idx][0]), int(bboxes[idx][1])),
                    (int(bboxes[idx][2]), int(bboxes[idx][3]))

                ])
                response['detection_scores'].append(str(scores[idx][0]))
            response_list.append(response)
    except Exception as e:
        print("error when predict model: ", e)
        sys.stderr.write(e)
        exit(1)
    return response_list


def covert_geojson(patch_set, response_list, output_path, img_geo_ref):
    try:
        geo_transform = [img_geo_ref.get("translateX"), img_geo_ref.get("scaleX"),
                         img_geo_ref.get("shearX"), img_geo_ref.get("translateY"),
                         img_geo_ref.get("shearY"), img_geo_ref.get("scaleY")]

        rect_list = get_rect_list(patch_set=patch_set, response_list=response_list)
        coord_list = get_coord_list(geo_transform=geo_transform, rect_list=rect_list)
        save_geojson(coord_list=coord_list, output_path=output_path)
    except Exception as e:
        print("error when save result to geojson: ", e)
        sys.stderr.write(e)
        exit(1)


def get_coord_list(geo_transform, rect_list):
    polygon_list = []
    for rect in rect_list:
        p1 = transform_coord(geo_transform, rect[0], rect[1])
        p2 = transform_coord(geo_transform, rect[0], rect[3])
        p3 = transform_coord(geo_transform, rect[2], rect[3])
        p4 = transform_coord(geo_transform, rect[2], rect[1])
        polygon_tup = ([p1, p2, p3, p4, p1],)
        polygon_list.append(polygon_tup)
    return polygon_list


def transform_coord(geo_transform, x, y):
    if geo_transform is not None:
        df_x = geo_transform[0] + geo_transform[1] * x + geo_transform[2] * y
        df_y = geo_transform[3] + geo_transform[4] * x + geo_transform[5] * y
        tup = (df_x, df_y)
        return tup
    else:
        tup = (x, y)
        return tup


def save_geojson(coord_list, output_path):
    feature_list = []
    for polygon_coords in coord_list:
        polygon = geojson.Polygon(polygon_coords)
        feature = geojson.Feature(geometry=polygon)
        feature_list.append(feature)
    fc = geojson.FeatureCollection(feature_list)
    with open(output_path, 'w') as f:
        geojson.dump(fc, f)


def get_rect_list(patch_set, response_list):
    shape = patch_set.shape
    index = 0
    rect_list = []
    for h in range(shape[0]):
        for w in range(shape[1]):
            shift_x = w * INPUT_SHAPE
            shift_y = h * INPUT_SHAPE
            bbox_list = response_list[index].get("detection_boxes")
            for box in bbox_list:
                shift_min_x = shift_x + box[0][0]
                shift_min_y = shift_y + box[0][1]
                shift_max_x = shift_x + box[1][0]
                shift_max_y = shift_y + box[1][1]
                rect_list.append([shift_min_x, shift_min_y, shift_max_x, shift_max_y])
            index += 1
    return rect_list


def split2list(str):
    if str is None:
        return None
    else:
        try:
            return str.split(",")
        except Exception as e:
            print("error when analyse parameters: ", e)
            sys.stderr.write(e)
            exit(1)


def obs_env_check():
    aws_env_list = ["ACCESS_KEY", "SECRET_KEY"]
    for env in aws_env_list:
        env_check(env)


def env_check(key):
    value = os.environ.get(key)
    if value is None:
        sys.stderr.write("environment variable for %s is not set.\n" % key)
        exit(1)


if __name__ == '__main__':
    cat_ids = None
    # 推理文件obs存储位置
    paths = 'obs://geogenius-public-bucket/geogenius/1577517737080/top_potsdam_2_11_RGBIR.tif'
    aoi = None
    # 推理结果本地存储位置
    output_path = '/tmp/test.geojson'
    car_detection_process(cat_ids=cat_ids, paths=paths, aoi=aoi, output_path=output_path)

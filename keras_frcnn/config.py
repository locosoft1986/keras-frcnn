from keras import backend as K
import os
from shutil import copy2
import pickle

class Config:
    def __init__(self):

        # additional input


        self.classes_count = None
        self.parser = None
        self.epoch_length = None
        self.num_epochs = None
        self.save_every = None

        self.current_epoch = 0 # number of current epoch (0 indexed)
                               # to pick up training later on.
        self.stats = []

        # more verbose output in training and test
        self.verbose = True

        # setting for data augmentation
        self.use_horizontal_flips = False
        self.use_vertical_flips = False
        self.rot_90 = False

        # anchor box scales
        self.anchor_box_scales = [128, 256, 512]

        # anchor box ratios
        self.anchor_box_ratios = [[1, 1], [1, 2], [2, 1]]

        # size to resize the smallest side of the image
        self.im_size = 600

        # image channel-wise mean to subtract
        self.img_channel_mean = [103.939, 116.779, 123.68]
        self.img_scaling_factor = 1.0

        # number of ROIs at once
        self.num_rois = 4

        # stride at the RPN (this depends on the network configuration)
        self.rpn_stride = 16

        self.balanced_classes = False

        # scaling the stdev
        self.std_scaling = 4.0
        self.classifier_regr_std = [8.0, 8.0, 4.0, 4.0]

        # overlaps for RPN
        self.rpn_min_overlap = 0.3
        self.rpn_max_overlap = 0.7

        # overlaps for classifier ROIs
        self.classifier_min_overlap = 0.1
        self.classifier_max_overlap = 0.5

        # placeholder for the class mapping, automatically generated by the parser
        self.class_mapping = None

        # location of pretrained weights for the base network
        # weight files can be found at:
        # https://github.com/fchollet/deep-learning-models/releases/download/v0.2/resnet50_weights_th_dim_ordering_th_kernels_notop.h5
        # https://github.com/fchollet/deep-learning-models/releases/download/v0.2/resnet50_weights_tf_dim_ordering_tf_kernels_notop.h5
        if K.image_dim_ordering() == 'th':
            self.base_net_weights = 'resnet50_weights_th_dim_ordering_th_kernels_notop.h5'
        else:
            self.base_net_weights = 'resnet50_weights_tf_dim_ordering_tf_kernels_notop.h5'

        self.model_name = 'model_frcnn.hdf5'
        self.config_filename = "config.pickle"
        self.output_folder = None  # has to be set to the run folder e.g. 'runs/YYYYMMDD-HHMMSS/'
        self.train_path = None     # has to be set to the txt containing the image annotations
        self.load_model = None     # from here training can be picked up
def create_config_read_parser(parser):
    parser.add_option("-p", "--path", dest="train_path",
                      help="Path to .txt training data (in case of simple parser).")
    parser.add_option("-r", "--resume", dest="resume_run",
                      help="Provide Path to folder or direct path to a config.pickle file")

    parser.add_option("--run", "--output_folder", dest="output_folder",
                      help="Specifies the folder that config etc is written into, if not provided " +
                           "will create new folder under runs/date-time/", )
    parser.add_option("--config_filename", dest="config_filename", help=
    "Location to store all the metadata related to the training (to be used when testing).",
                      default="config.pickle")
    parser.add_option("--output_weight_path", dest="output_weight_path", help="Output path for weights.",
                      default='model_frcnn.hdf5')
    parser.add_option("--input_weight_path", dest="input_weight_path",
                      help="Input path for weights. If not specified, will try to load default weights provided by keras.")
    parser.add_option("--save_every", dest="save_every",
                      help="will save n epochs", default=100)

    parser.add_option("-o", "--parser", dest="parser", help="Parser to use. One of simple or pascal_voc",
                      default='simple')  # '#default="pascal_voc"),
    parser.add_option("-n", "--num_rois", dest="num_rois",
                      help="Number of ROIs per iteration. Higher means more memory use.",
                      default=32)
    parser.add_option("--hf", dest="horizontal_flips",
                      help="Augment with horizontal flips in training. (Default=false).",
                      action="store_true", default=False)
    parser.add_option("--vf", dest="vertical_flips", help="Augment with vertical flips in training. (Default=false).",
                      action="store_true", default=False)
    parser.add_option("--rot", "--rot_90", dest="rot_90",
                      help="Augment with 90 degree rotations in training. (Default=false).",
                      action="store_true", default=False)
    parser.add_option("--num_epochs", dest="num_epochs", help="Number of epochs.",
                      default=1000)  # 2000
    parser.add_option("--epoch_length", dest="epoch_length", help="Number of batches in an epoch",
                      default=1000)  # 2000
    parser.add_option("--verbose", dest="verbose",
                      help="Additional Output is shown, possible values 0 or 1.",
                      default='0')
    parser.add_option("--store", dest="store",
                      help="how is the output stored 'tensorboard', 'txt'")
    parser.add_option("--frcnn_weights", dest="frcnn_weights",
                      help="starts a new training/config file but will load in the weights from an older training")

    (options, args) = parser.parse_args()

    # resume training with old configuration
    run_path = options.resume_run if options.resume_run != '.last' else "runs/"+sorted(os.listdir("runs/"))[-1] +"/"
    if run_path:
        if run_path[-1] != '/':
            run_path += '/'
        print("Resuming from", run_path)
        with open(run_path + "config.pickle", 'rb') as config_f:
            C = pickle.load(config_f)
        C.output_folder = run_path
        C.load_model = run_path + C.model_name
        if C.verbose:
            print("Resume Training on epoch", C.current_epoch + 1)
        if options.num_epochs:
            C.num_epochs = int(options.num_epochs)
            print("Reset #epochs to", C.num_epochs)
        if options.epoch_length:
            C.epoch_length = int(options.epoch_length)
            print("Reset epoch_length to", C.epoch_length)
        if options.train_path:
            C.train_path = options.train_path
            print("Reset train_path to", C.train_path)


        return C

    # pass the settings from the command line, and persist them in the config object
    C = Config()
    C.config_filename = options.config_filename
    C.num_rois = int(options.num_rois)
    C.use_horizontal_flips = bool(options.horizontal_flips)
    C.use_vertical_flips = bool(options.vertical_flips)
    C.rot_90 = bool(options.rot_90)

    C.epoch_length = int(options.epoch_length)
    C.num_epochs = int(options.num_epochs)
    C.parser = options.parser
    C.save_every = options.save_every

    if not options.train_path:  # if filename is not given
        parser.error('Error: path to training e.g. "annotations/bb.txt" data must be specified. Pass --path to command line')
    C.train_path = options.train_path

    # specify the folder in which all the meta data is stored.
    if not options.output_folder:  # set it to current date/time
        import time
        C.output_folder = time.strftime("runs/%Y%m%d-%H%M%S/")
    else:
        C.output_folder = options.output_folder
        if not os.path.exists(C.output_folder):
            input("Output folder" + str(C.output_folder) + "doesn't exist. Press any key to create it.")
    os.makedirs(C.output_folder)
    copy2(options.train_path, C.output_folder)


    # specify input and output of weights
    if options.input_weight_path:
        C.base_net_weights = options.input_weight_path  # the original ResNet model
    if options.frcnn_weights:
        C.load_model = options.frcnn_weights
    else:
        C.load_model = None  # this will actually be loaded, might change when training is resumed
    C.model_name = options.output_weight_path  # within run folder



    return C
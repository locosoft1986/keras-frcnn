import os
import csv
import config

""" Convert the notations form the following datasets to be used with Keras-frcnn in the simple data reader mode
the 3D bounding boxes form VehicleReI dinto a front and a back bounding box. """

#PATH_VEHICLEREID = "/disk/ml/datasets/VehicleReId/"
PATH_VEHICLEREID = config.PLATTE_BASEPATH + "VehicleReId/video_shots/"
#PATH_CITYSCAPES = "/disk/ml/datasets/cityscapes/"
#PATH_BOXCARS = "/disk/ml/datasets/BoxCars21k/"

LIMIT_OUTPUT = 1000 # only write the first n entries or "" for no limit

OUTPUT_FILE = config.PROJECTS_BASEPATH + "scripts/bb"+str(LIMIT_OUTPUT)+".txt"
TARGET_PATH = "images/"  # no spaces possible here!
TARGET_NUMBER_FORMAT = '%05d'
TARGET_SUFFIX = '.png'

counter = 0
with open(OUTPUT_FILE, 'w+') as outfile:
    fieldnames = ["filepath", "x1", "y1", "x2", "y2", "class_name"]
    csvwriter = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=',', lineterminator='\n')
    print("write to", OUTPUT_FILE)

    for shot_name in ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B", "5A", "5B"]:
        if counter == 'break': break
        anno_file = PATH_VEHICLEREID + shot_name + "_annotations.txt"
        if not os.path.isfile(anno_file):
            print("Annotation File:", anno_file, "doesn't exist, skip")
            continue
        with open(anno_file, 'r') as file:
            csvreader = csv.reader(file, delimiter=',')
            for line in csvreader:
                if counter != "":
                    counter += 1
                    if counter >= LIMIT_OUTPUT:
                        print("Successfully finished after", counter, "entries")
                        counter = 'break'
                        break
                try:
                    (carId, frame,
                     upperPointShort_x, upperPointShort_y,      #red
                     upperPointCorner_x, upperPointCorner_y,    #yellow
                     upperPointLong_x, upperPointLong_y,        #white
                     crossCorner_x, crossCorner_y,              #cyan
                     shortSide_x, shortSide_y,                  #blue
                     corner_x, corner_y,                        #black
                     longSide_x, longSide_y,                    #green
                     lowerCrossCorner_x, lowerCrossCorner_y     #purple
                     ) = [int(entry) for entry in line]
                except ValueError:
                    print("Warning: invalid line in:", line)
                    continue
                frame_path = TARGET_PATH + shot_name + "_" + TARGET_NUMBER_FORMAT % frame + TARGET_SUFFIX

                # outer boundingbox: top left and bottom right corner
                # (green_x, cyan_y) - (red_x, black_y)
                csvwriter.writerow({
                    "filepath": frame_path,
                    "x1": longSide_x,        "y1": crossCorner_y,
                    "x2": upperPointShort_x, "y2": corner_y,
                    "class_name": "outerBB"
                                  })
                # front boundingbox: described by red and black
                # (black_x, red_y) - (red_x, black_y)
                csvwriter.writerow({
                    "filepath": frame_path,
                    "x1": corner_x,        "y1": upperPointShort_y,
                    "x2": upperPointShort_x, "y2": corner_y,
                    "class_name": "frontBB"
                })
                # (facing) side boundingbox: described by white and black
                # (white_x, white_y) - (black_x, black_y)
                csvwriter.writerow({
                    "filepath": frame_path,
                    "x1": corner_x,        "y1": upperPointShort_y,
                    "x2": upperPointShort_x, "y2": corner_y,
                    "class_name": "sideBB"
                })
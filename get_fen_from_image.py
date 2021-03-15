# assume this is run after detect.py has been run, this means that the images in data/images
# have corresponding data in labels
from PIL import Image
import numpy as np
import pandas as pd
import os
import random
import sklearn
import skimage
import skimage.io
import matplotlib.pyplot as plt
import detect
import time

PROJECT_DIR =  "/home/alaird/personal/StreamlineChessTutor/"
INPUT_DIR =  PROJECT_DIR + 'data/input_images'
TO_CROP_LABELS_DIR =  PROJECT_DIR + 'data/cropped/labels'
CROPPED_DIR  = PROJECT_DIR + 'data/cropped'
OUTPUT_DIR = 'data/output_fen'

CROP_MODEL = PROJECT_DIR + 'cropModel.pt'
PIECE_MODEL = PROJECT_DIR + 'pieceModel.pt'


# rename input files to be 1->N
detected_files = []
for (dirpath, dirnames, filenames) in os.walk(INPUT_DIR):
    for i,file in enumerate(filenames):
        new_filename = str(i+1)+'.png'
        os.rename(INPUT_DIR+'/'+file, INPUT_DIR + '/' + new_filename)
        detected_files.append(new_filename)
    break

# start off by running the crop model on the input images
detect.detect(INPUT_DIR, CROP_MODEL, CROPPED_DIR)

# this puts labels in the crop_dir that we use to actually crop the images

def map_files_to_labels(image):
    text_path = image.split('.')[0] + ".txt"
    return text_path

labels = [map_files_to_labels(file) for file in detected_files]

def crop_image(file,label, output_filename, output_dir):
    width, height = image.size
    # find the most confident of the chessboards here
    # but for now just get the first one
    possible_chessboards = [[float(x) for x in list(label[i])[0].split(' ')] for index in label.iterrows()]
    most_confident_chessboard = sorted(possible_chessboards, key=lambda row: row[5])[0]
    class_id, center_x, center_y,  box_width, box_height, confidence = most_confident_chessboard
    pixel_center_x = width*center_x
    pixel_center_y = height*center_y
    pixel_box_width = width*box_width
    pixel_box_height = height*box_height
    box_top_left_x = pixel_center_x - pixel_box_width/2
    box_top_left_y = pixel_center_y - pixel_box_height/2



    left = box_top_left_x
    top= box_top_left_y
    right =  (box_top_left_x + pixel_box_width )
    bottom = (box_top_left_y + pixel_box_height )
    cropped_image = image.crop((left, top, right, bottom))
    cropped_image = cropped_image.resize((1200,1200))

    #image.show()
    cropped_image.save(output_dir + "/" + output_filename)

for i in range(len(detected_files)):
    image = Image.open(INPUT_DIR + '/' + detected_files[i])
    if( not os.path.exists(TO_CROP_LABELS_DIR + "/" +labels[i])):
        continue
    label = pd.read_csv(TO_CROP_LABELS_DIR + "/" +labels[i], header=None)
    crop_image(image,label,detected_files[i],CROPPED_DIR)

# then we run those cropped images through the piece model
detect.detect(CROPPED_DIR, PIECE_MODEL, OUTPUT_DIR)



# this outputs files that we can process into the final chess board!
fen_array  = ['P','N','B','R','K','Q','p','n','b','r','k','q']
def board_to_fen(board):
    fen_str = ''
    for y in range(8):
        if(y>0):
            fen_str += '/'
        row = board[y]
        counter = 0
        row_str = ""
        for x in range(8):
            piece = row[x]
            if(piece == 12):
                counter += 1
            else:
                if(counter != 0):
                    row_str += str(counter)
                    counter = 0
                row_str+= fen_array[int(piece)]
        if(counter != 0):
            row_str += str(counter)
        fen_str += row_str

    #who's turn is it
    fen_str += " w"

    #who can castle and what was the last move
    fen_str += ' - -'
    print("FEN:",fen_str)


for i in range(len(detected_files)):
    board_labels = pd.read_csv(OUTPUT_DIR+'/labels/'+labels[i], header=None, sep=' ')
    # intialize the boards all empty
    combined_confidence = 0
    total_number_of_pieces = 0
    board = [[12 for x in range(8)] for y in range(8)]
    for index, piece in board_labels.iterrows():
        class_id, center_x, center_y,  box_width, box_height, confidence = [float(x) for x in piece]
        if(confidence < .85):
            continue
        combined_confidence += confidence
        # split the center_x/y into the 8th it belongs in
        x_pos = int(center_x // (.125))
        y_pos = int(center_y // (.125))
        board[y_pos][x_pos] = class_id
        total_number_of_pieces += 1
    board_to_fen(board)


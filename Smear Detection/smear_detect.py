import argparse
import cv2
import os
import numpy as np

# flags
parser = argparse.ArgumentParser(description = "Parameters")
parser.add_argument('--out', default = "", help = "The path to save the outputs")
parser.add_argument('--path', default = "", help = "The path of the pictures to look for smears")

FLAGS = parser.parse_args()

#path = lambda x: f"{x}-{FLAGS.path.replace('/', '_')}.jpg" if not FLAGS.out else f"{FLAGS.out + ('/' if not FLAGS.out.endswith('/') else '')}{x}_{FLAGS.path.replace('/', '_')}.jpg"
path = lambda x: f"{FLAGS.path.replace('/', '_')}/{x}.jpg" if not FLAGS.out else f"{FLAGS.out + ('/' if not FLAGS.out.endswith('/') else '')}{FLAGS.path.replace('/', '_')}/{x}.jpg"

if not FLAGS.path or not os.path.isdir(FLAGS.path):
    print("Path to pictures not provided. Please provide path. Example: --path pics/")
    exit()
if FLAGS.out:
    os.path.isdir(FLAGS.out) or os.makedirs(FLAGS.out)

def path1(im):
    p = path(im)
    os.path.isdir(p[:p.rfind('/')]) or os.makedirs(p[:p.rfind('/')])
    return p

def process(image):
    """
    Every image -> grayscale -> adaptive threshold -> dilate
    """
    img = cv2.imread(os.path.join(FLAGS.path, image))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #_, thresh = cv2.threshold(gray, 122, 255, cv2.THRESH_BINARY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 275, 5) # was 275, 10
    kernel = np.ones((3, 3), np.uint8)
    dilate = cv2.dilate(thresh, kernel, iterations = 1)
    #can = cv2.Canny(dilate, 122, 140)
    #cv2.imwrite('can.jpg', can)
    #cv2.imwrite('thresh.jpg', thresh)
    #cv2.imwrite('dilate.jpg', dilate)
    return dilate

def intermediates(images):
    """
    Creates intermediate images; (total images / 8) images averaged
    """

    i = 1
    intms = []
    for parts in images:
        summ = 0
        for image in parts:
            out = process(image)
            summ += out / len(parts)
        cv2.imwrite(path1(f'Intermediate_{i}'), summ)
        intms.append(path1(f'Intermediate_{i}'))
        i += 1
    return intms

def intm_processing(images):
    """
    Modify intermediates -> grayscale -> adaptive threshold -> inverse
    """

    i = 1
    f_intm = []
    for image in images:
        img = cv2.imread(image)
        fin = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        fin = cv2.adaptiveThreshold(fin,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY, 101, 11)
        #clahe = cv2.createCLAHE(clipLimit = 5)
        #clah = clahe.apply(gray)
        #clah = cv2.adaptiveThreshold(clah,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY, 255, 70)
        #cv2.imwrite(path1(f"fin_inter_{i}"), clah)
        # fin = gray
        # kernel = np.ones((3,3), np.uint8)
        # er = cv2.erode(fin, kernel, iterations = 5)
        # fin = cv2.dilate(er, kernel, iterations = 5)
        # _, thresh = cv2.threshold(fin, 122, 255, cv2.THRESH_BINARY)
        # adapt = cv2.adaptiveThreshold(fin,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY, 45, 5)
        # fin = thresh
        # can = cv2.Canny(gray, 111, 150)
        fin = cv2.bitwise_not(fin)
        cv2.imwrite(path1(f"fin_inter_{i}"), fin)
        f_intm.append(path1(f"fin_inter_{i}"))
        i += 1
    return f_intm

def final_processing(images):
    """
    Average intermediates -> grayscale -> threshold using most white -> dilate af
    """

    final = 0
    for image in images:
        img = cv2.imread(image)
        final += img / len(images)

    #final = cv2.bitwise_not(final)
    cv2.imwrite(path1("FINAL"), final)
    final = cv2.imread(path1("FINAL"))
    final = cv2.cvtColor(final, cv2.COLOR_BGR2GRAY)
    #final = cv2.adaptiveThreshold(final,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY, 121, 25)
    low = np.floor(max(final.flatten())) - 5
    _, final = cv2.threshold(final, low, 255, cv2.THRESH_BINARY)
    kernel = np.ones((3,3), np.uint8)
    final = cv2.dilate(final, kernel, iterations = 22)
    cv2.imwrite(path1("FINAL_1"), final)


def main():

    # get images -- split to 8
    images = os.listdir(FLAGS.path)
    n = int((len(images) / 8) + 1)
    subs = [images[i * n: (i + 1) * n] for i in range((len(images) + n - 1) // n)]

    intm = intermediates(subs)

    #intm = [path1(f"Intermediate_{i}") for i in range(1,9)]
    f_intm = intm_processing(intm)

    final_processing(f_intm)

if __name__ == "__main__":
    main()
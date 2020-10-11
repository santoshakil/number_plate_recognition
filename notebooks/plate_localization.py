import pytesseract
import cv2
import random
import os
import numpy as np
import matplotlib.pyplot as plt

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import sqlite3


images_dir = "data/images"
image_files = os.listdir(images_dir)
t = time.strftime('%Y-%m-%d %H:%M:%S')


def database(time, number):
    try:
        data = [time, number]
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS main (time DATETIME, number INTEGER)''')
        print("Successfully Connected to Database")

        cursor.execute('''INSERT INTO main VALUES (?, ?) ''', data)

        connection.commit()
        print("Record inserted successfully into Database table ", cursor.rowcount)
        cursor.close()

    except sqlite3.Error as error:
        print("Failed to insert data into sqlite table", error)


def detect(image_path):

    #image_path = "{}/{}".format(images_dir, "car_1.jpg")

    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def plot_images(img1, img2, title1="", title2=""):
        fig = plt.figure(figsize=[15, 15])
        ax1 = fig.add_subplot(121)
        ax1.imshow(img1, cmap="gray")
        ax1.set(xticks=[], yticks=[], title=title1)

        ax2 = fig.add_subplot(122)
        ax2.imshow(img2, cmap="gray")
        ax2.set(xticks=[], yticks=[], title=title2)

    plot_images(image, gray)

    blur = cv2.bilateralFilter(gray, 11, 90, 90)

    plot_images(gray, blur)

    edges = cv2.Canny(blur, 30, 200)

    plot_images(blur, edges)

    cnts, new = cv2.findContours(
        edges.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    image_copy = image.copy()

    _ = cv2.drawContours(image_copy, cnts, -1, (255, 0, 255), 2)

    plot_images(image, image_copy)

    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:30]

    image_copy = image.copy()
    _ = cv2.drawContours(image_copy, cnts, -1, (255, 0, 255), 2)

    plot_images(image, image_copy)

    plate = None
    for c in cnts:
        perimeter = cv2.arcLength(c, True)
        edges_count = cv2.approxPolyDP(c, 0.02 * perimeter, True)
        if len(edges_count) == 4:
            x, y, w, h = cv2.boundingRect(c)
            plate = image[y:y+h, x:x+w]
            break

    cv2.imwrite("plate.png", plate)

    plot_images(plate, plate)

    text = pytesseract.image_to_string(plate, lang="eng")

    print(text)

    database(t, text)


################################################################


class Watcher:
    DIRECTORY_TO_WATCH = images_dir

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(
            event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            print("Received created event - %s." % event.src_path)
            detect(event.src_path)

        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            print("Received modified event - %s." % event.src_path)


if __name__ == '__main__':
    w = Watcher()
    w.run()


################################################################

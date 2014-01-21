# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Parses a Sudoku puzzle image, converts the puzzle to a string of numbers.

Code modified from the following sources:
- http://goo.gl/baijxj
- http://goo.gl/8O3obH
"""

__author__ = 'kbrisbin@google.com (Kathryn Hurley)'

import cv
import cv2
import numpy as np


GREEN = (0, 255, 0)
SUDOKU_RESIZE = 450
NUM_ROWS = 9
JPEG_EXTENSION = '.jpeg'
TEXT_WEIGHT = 2
TEXT_SIZE = 1
XOFFSET = 20
YOFFSET = 35


class SudokuImageParser(object):
    """Parses a sudoku puzzle.

    Attributes:
        model: cv2.KNearest model trained with OCR data.
        image: numpy.ndarray of the original Sudoku image.
        resized_largest_square: numpy.ndarray of the largest square in the
            image.
        stringified_puzzle: The puzzle as a string of numbers.
    """

    def __init__(self):
        """Initialize the SudokuImageParser class and model."""

        self.model = self._get_model()

    def parse(self, image_data):
        """Parses the image file and returns the puzzle as a string of numbers.

        Args:
            image_data: The data of the image as a string.

        Returns:
            String of numbers representing the Sudoku puzzle.
        """

        self.image = self._create_image_from_data(image_data)
        largest_square = self._find_largest_square()
        self.resized_largest_square = self._resize(
                largest_square, SUDOKU_RESIZE)
        puzzle = self._get_puzzle()
        self.stringified_puzzle = ''.join(str(n) for n in puzzle.flatten())
        return self.stringified_puzzle

    def draw_solution(self, solution):
        """Draw the solution to the puzzle on the image.

        Args:
            solution: An np array containing the solution to the puzzle.

        Returns:
            The numpy.ndarray with the solution.
        """

        for i in xrange(len(self.stringified_puzzle)):
            if self.stringified_puzzle[i] == '0':
                r = i / NUM_ROWS
                c = i % NUM_ROWS
                loc = SUDOKU_RESIZE / NUM_ROWS
                posx = c*loc + XOFFSET
                posy = r*loc + YOFFSET
                cv2.putText(
                        self.resized_largest_square,
                        solution[i],
                        (posx, posy),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        TEXT_SIZE,
                        GREEN,
                        TEXT_WEIGHT)

        return self.resized_largest_square

    def convert_to_jpeg(self, nparray):
        """Converts a numpy array to a jpeg cv2.Mat image.

        Args:
            nparray: A numpy.ndarray of an image.

        Returns:
            A cv2.Mat jpeg-encoded image.
        """

        cvmat = cv.fromarray(nparray)
        cvmat = cv.EncodeImage(JPEG_EXTENSION, cvmat)
        return cvmat

    def _create_image_from_data(self, image_data):
        """Convert string image data to cv2.Mat.

        Args:
            image_data: The data of the image as a string.

        Returns:
            A numpy.ndarray representing the image.
        """

        np_array = np.fromstring(image_data, np.uint8)
        image = cv2.imdecode(np_array, cv2.CV_LOAD_IMAGE_COLOR)
        return image

    def _get_model(self):
        """Return the OCR model using training data and samples.

        Returns:
            Trained cv2.KNearest model.
        """

        samples = np.float32(np.loadtxt('feature_vector_pixels.data'))
        responses = np.float32(np.loadtxt('samples_pixels.data'))

        model = cv2.KNearest()
        model.train(samples, responses)
        return model

    def _find_largest_square(self):
        """Find the largest square in the image, most likely the puzzle.

        Returns:
            Contour vector with the largest area or None if not found.
        """

        contours, image = self._get_major_contours(self.image)

        # Store contours that could be the puzzle using the contour's area
        # as the key.
        possible_puzzles = {}

        for contour in contours:
            contour_length = cv2.arcLength(contour, True)
            area = cv2.contourArea(contour)

            # Approximate the contour to a polygon.
            contour = cv2.approxPolyDP(contour, 0.02 * contour_length, True)

            # Find contours with 4 vertices and an area greater than a
            # third of the image area with a convex shape.
            if len(contour) == 4 and (
                    area > image.size / 3.0 and cv2.isContourConvex(contour)):

                # Find the largest cosine of the angles in the contour.
                contour_reshaped = contour.reshape(-1, 2)
                max_cos = np.max([self._angle_cos(
                        contour_reshaped[i],
                        contour_reshaped[(i+1) % 4],
                        contour_reshaped[(i+2) % 4]) for i in xrange(4)])

                # If the max cosine is almost zero (a square),
                # it is most likely the Sudoku puzzle.
                if max_cos < 0.1:
                    possible_puzzles[area] = contour

        # We get the smallest contour because sometimes interference around the
        # edge of the image creates a contour almost the size of the image,
        # and we don't want to use that contour.
        areas = possible_puzzles.keys()
        areas.sort()
        return possible_puzzles[areas[0]]

    def _get_puzzle(self):
        """Get the numbers in the puzzle in a 9x9 array.

        Returns:
            A numpy.ndarray filled with the numbers of the puzzle.
        """

        # a 9x9 matrix to store our sudoku puzzle
        sudoku_matrix = np.zeros((NUM_ROWS, NUM_ROWS), np.uint8)

        contours, image_copy = self._get_major_contours(
                self.resized_largest_square,
                sigma1=3,
                threshold_type=cv2.THRESH_BINARY_INV,
                dilate=False)

        # Erode and dilate the image to further amplify features.
        kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        erode = cv2.erode(image_copy, kernel)
        dilate = cv2.dilate(erode, kernel)

        for contour in contours:
            area = cv2.contourArea(contour)

            if 100 < area < 800:
                (bx, by, bw, bh) = cv2.boundingRect(contour)
                if (100 < bw*bh < 1200) and (10 < bw < 40) and (25 < bh < 45):
                    # Get the region of interest, which contains the number.
                    roi = dilate[by:by + bh, bx:bx + bw]
                    small_roi = cv2.resize(roi, (10, 10))
                    feature = small_roi.reshape((1, 100)).astype(np.float32)

                    # Use the model to find the most likely number.
                    ret, results, neigh, dist = self.model.find_nearest(
                            feature, k=1)
                    integer = int(results.ravel()[0])

                    # gridx and gridy are indices of row and column in Sudoku
                    gridy = (bx + bw/2) / (SUDOKU_RESIZE / NUM_ROWS)
                    gridx = (by + bh/2) / (SUDOKU_RESIZE / NUM_ROWS)
                    sudoku_matrix.itemset((gridx, gridy), integer)

        return sudoku_matrix

    def _get_major_contours(
            self, image, sigma1=0, dilate=True,
            threshold_type=cv2.THRESH_BINARY):
        """Simplifies the image to find and return the major contours.

        Args:
            image: numpy.ndarray representing the image.
            sigma1: Integer Gaussian kernel standard deviation in X direction.
            dilate: Boolean for dilating the image.
            threshold_type: Integer representing the thresholding type.

        Returns:
            List of contours and the numpy.ndarray modified image.

        Raises:
            ImageError if image could not be processed.
        """

        try:
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        except cv2.error as e:
            raise ImageError('Could not process image.')

        mod_image = cv2.GaussianBlur(gray_image, ksize=(3, 3), sigma1=sigma1)
        if dilate:
            mod_image = cv2.dilate(
                    mod_image,
                    kernel=cv2.getStructuringElement(
                            shape=cv2.MORPH_RECT, ksize=(3, 3)))
        mod_image = cv2.adaptiveThreshold(
                mod_image,
                maxValue=255,
                adaptiveMethod=cv2.ADAPTIVE_THRESH_MEAN_C,
                thresholdType=threshold_type,
                blockSize=5,
                C=2)

        copied_image = mod_image.copy()
        contours, hierarchy = cv2.findContours(
                mod_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        return contours, copied_image

    def _angle_cos(self, p0, p1, p2):
        """Find the cosine of the angle.

        Args:
            p0: List representing the coordinates one corner of the square.
            p1: List representing the coordinates one corner of the square.
            p2: List representing the coordinates one corner of the square.

        Returns:
            The float cosine of the angle between the 3 coordinates.
        """

        d1 = (p0 - p1).astype('float')
        d2 = (p2 - p1).astype('float')
        return abs(np.dot(d1, d2) / np.sqrt(np.dot(d1, d1) * np.dot(d2, d2)))

    def _resize(self, square, size):
        """Resize the sudoku puzzle to specified dimension.

        Args:
            square: The cv2.Mat image to resize.
            size: The integer value to resize the image to.

        Returns:
            The resized numpy.ndarray of the image.
        """

        # Put the corners of square in clockwise order.
        approx = self._rectify(square)

        h = np.array(
                [[0, 0], [size - 1, 0], [size - 1, size - 1], [0, size - 1]],
                np.float32)

        # Get the transformation matrix.
        tranformed_image = cv2.getPerspectiveTransform(approx, h)

        # Use the transformation matrix to resize the square to the
        # specified size.
        resized_image = cv2.warpPerspective(
                self.image, tranformed_image, (size, size))

        return resized_image

    def _rectify(self, square):
        """Put vertices of square in clockwise order.

        Args:
            square: List of vertices representing a square.

        Returns:
            List of vertices of the square in clockwise order.
        """

        square = square.reshape((4, 2))
        square_new = np.zeros((4, 2), dtype=np.float32)

        add = square.sum(1)
        square_new[0] = square[np.argmin(add)]
        square_new[2] = square[np.argmax(add)]

        diff = np.diff(square, axis=1)
        square_new[1] = square[np.argmin(diff)]
        square_new[3] = square[np.argmax(diff)]

        return square_new


class ImageError(Exception):
    """Raised when image could not be processed."""

import numpy as np
from PIL import ImageFont, ImageDraw, Image
import cv2

def set_image():
    font = ImageFont.truetype("fonts/gulim.ttc", 20)

    img = np.full((600,800,3), (255,255, 255), np.uint8)
    img = Image.fromarray(img)

    draw = ImageDraw.Draw(img)
    text = '           지도    가방 안에 넣고서'
    text2 = '때 묻은       는                        '

    draw.text((30, 50), text, font=font, fill=(0,0,255))
    draw.text((30, 50), text2, font=font, fill=(0,0,0))

    img = np.array(img)

    cv2.namedWindow('text')
    cv2.imshow("text", img)

    cv2.waitKey()
    cv2.destroyAllWindows()

def main():
    set_image()
    
if __name__ == '__main__':
    main()
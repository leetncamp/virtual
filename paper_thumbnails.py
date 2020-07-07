import PyPDF2

from PIL import Image
import os
from pdb import set_trace as debug
from multiprocessing import Pool
import fitz
from PIL import Image

"""Create .jpg thumbnails of papers.pdfs. PNG temp files are not erased in case they're useful"""

desired_image_height = 720 #px


get_image = {
    
}

def get_first_image_from_pdf(pdf_path):



    doc = fitz.open(pdf_path)
    dirname = os.path.dirname(pdf_path)
    count = 1
    print(pdf_path)

    for i in range(len(doc)):
        print("Page {}".format(i))
        im_list = doc.getPageImageList(i)

        for img in im_list:

            get_image_number = get_image.get(os.path.basename(pdf_path))

            if get_image_number and count != get_image_number:
                count += 1
                continue
            else:
                png_path = os.path.join(dirname, pdf_path.replace("Paper.pdf", "PaperImage.png"))
                xref = img[0]
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n < 5:       # this is GRAY or RGB
                        pix.writePNG(png_path)
                    else:               # CMYK: convert to RGB first
                        pix1 = fitz.Pixmap(fitz.csRGB, pix)
                        pix1.writePNG(png_path)
                        pix1 = None
                    pix = None
                except:
                    return()
                

                im = Image.open(png_path)
                image_large_enough = im.size[0] > 100 and im.size[1] > 100
                aspect_ratio_ok = 0.3 < im.size[0] / im.size[1] > 3

                #if image_large_enough and aspect_ratio_ok:
                if True:
                    scale = desired_image_height / im.size[0]
                    size = (int(im.size[0] * scale), int(im.size[1] * scale ))
                    im_resized = im.resize(size, Image.ANTIALIAS)
                    jpg_path = os.path.join(os.path.splitext(pdf_path)[0] + "Thumbnail.jpg")
                    try:
                        im_resized.save(jpg_path, "JPEG")
                    except:
                        im_converted = im.convert('RGB')
                        im_converted.save(jpg_path, "JPEG")

                    print(png_path)
                    return
                else:
                    pass
                    #print("BAD IMAGE SIZE")
                count += 1


    


if __name__ == "__main__":
    from argparse import ArgumentParser
    import glob
    parser = ArgumentParser()
    parser.add_argument("folder")
    ns = parser.parse_args()
    pdfs = sorted(glob.glob(os.path.join(ns.folder, "*.pdf")))
    
    if False:
        for pdf_path in pdfs:
            get_first_image_from_pdf(pdf_path)
    else:
        p = Pool()
        p.map(get_first_image_from_pdf, pdfs)

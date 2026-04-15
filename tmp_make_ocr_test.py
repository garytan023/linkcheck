from PIL import Image, ImageDraw
img = Image.new('RGB',(1200,260),'white')
d = ImageDraw.Draw(img)
d.text((40,40),'Hello OCR 123', fill='black')
d.text((40,120),'测试 本地 OCR 能力', fill='black')
img.save('/tmp/ocr_local_test.png')
print('/tmp/ocr_local_test.png')

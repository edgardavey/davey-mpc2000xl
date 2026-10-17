import sys,glob
from PIL import Image
files=sorted(glob.glob(sys.argv[1]+'/*.png'))[-int(sys.argv[3]) if len(sys.argv)>3 else None:]
ims=[Image.open(f).convert('RGB') for f in files]
w,h=ims[0].size; s=3
out=Image.new('RGB',(w*s,(h*s+6)*len(ims)),'white')
for i,im in enumerate(ims): out.paste(im.resize((w*s,h*s),Image.NEAREST),(0,i*(h*s+6)))
out.save(sys.argv[2]); print(len(ims),'frames',w,h)

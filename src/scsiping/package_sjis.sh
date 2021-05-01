# I converted all of these files to UTF-8 for easier viewing on modern systems.
# This script converts the files to Shift-JIS for use on a NEWS system.
# Before running this script, ensure that `nkf` is installed and in PATH.
mkdir scsiping-sjis/
for file in scsi.c Makefile Readme scsi.jman scsi.man
do
    nkf -s $file > scsiping-sjis/$file
done
tar -cf scsiping-sjis.tar scsiping-sjis/
rm -rf scsiping-sjis/


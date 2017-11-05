import sys
import os
import platform
from subprocess import call
import getpass
import urllib
import urllib2

#Set vars
s3bucket = raw_input("Enter your S3 bucketname:\n").strip()
private_key = raw_input("Enter your IAM Private Key:\n").strip()
secret_key = raw_input("Enter your IAM Secret Key:\n").strip()
mount_path = "/mnt/s3"
cache_path = "/tmp/cache"
deb_packages = "git automake build-essential libcurl4-openssl-dev libxml2-dev pkg-config libssl-dev libfuse-dev"
rhel_packages = "git make openssl-devel gcc libstdc++-devel gcc-c++ curl-devel libxml2-devel mailcap automake"
user = getpass.getuser()

#Install required packages based on OS
os_platform = platform.system()
rhel = os.path.exists("/etc/redhat-release")
deb = os.path.exists("/etc/lsb-release")
rhel_fuse_url = 'https://github.com/libfuse/libfuse/releases/download/fuse-2.9.7/fuse-2.9.7.tar.gz'
rhel_fuse_tar = "/usr/src/fuse-2.9.7.tar.gz"

if os_platform == "Linux":
    if deb == True:
        call("apt-get update",shell=True)
        call("apt-get install -y " + deb_packages, shell=True)
    elif rhel == True:
        call("yum update -y",shell=True)
        call("yum install -y "+ rhel_packages, shell=True)
        call("yum erase -y fuse fuse-s3fs",shell=True)
        os.system("export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig")
        urllib.urlretrieve(rhel_fuse_url,filename=rhel_fuse_tar)
        call("cd /usr/src && tar xzf fuse-2.9.7.tar.gz",shell=True)
        call("cd /usr/src/fuse-2.9.7 && ./configure --prefix=/usr/local",shell=True)
        call("cd /usr/src/fuse-2.9.7 && make && make install",shell=True)
        call("ldconfig && modprobe fuse",shell=True)
        
    else:
        print("This is not a Linux OS. Please consult s3fs documentation for instuctions specic to your OS") 
else:
    print("This script does not support your Operating System at this time")

#Get user info and set home
if user == "root":
    user_home = "/root"
else:
    user_home = "/home/" + getpass.getuser()

#Clone Git Repo, write passwd file
call("echo "+ private_key + ':' + secret_key + " > " + user_home + "/.passwd-s3fs", shell=True)
os.chmod(user_home + "/.passwd-s3fs",0600)
call("cd " + user_home + " && git clone https://github.com/s3fs-fuse/s3fs-fuse", shell=True)
call("cd ~/s3fs-fuse && /bin/bash ./autogen.sh",shell=True)
call("cd ~/s3fs-fuse && /bin/bash ./configure --prefix=/usr --with-openssl",shell=True)
call("cd ~/s3fs-fuse && make && make install",shell=True)
#Create and mount dirs
os.mkdir(mount_path)
os.mkdir(cache_path)
os.chmod(cache_path,0777)
call("s3fs -o allow_other,use_cache=" + cache_path + ' ' + s3bucket + ' ' + mount_path,shell=True)
print("to add the s3 bucket to fstab enter the follwing into /etc/fstab\n")
print("s3fs#"+ s3bucket + " /mnt/s3 fuse allow_other,use_cache=/tmp/cache 0 0")

"""
图片使用img引用

打开80端口，直接使用http网站访问主机下的文件夹，也能显示图片？

web服务器根据请求的URL路径，找到主机文件系统中对应的文件

文件传输，web服务器将找到的文件通过http协议发送回到客户端浏览器。浏览器根据文件的MIME类型正确的显示或处理该文件

安全性
可移植性
访问控制

最好的方式是服务端和图片搜索端分离，图片搜索端用于存储图片和返回图片候选列表，提供的是图片公网访问链接。
#使用http公网地址直接获取主机的访问权限，而不用重开一个端口。
#使用域名则先注册一个域名，然后解析到服务器的IP地址。
#web服务器的静态文件目录，可以使用默认文件目录，或者配置web服务器自定义图片目录：apache、nginx
"""
#-------------------image_api示例--------------------

#-------------------该示例仅供单机测试使用，不推荐在生产环境中使用。首先应有一个公网ip或者本地测试时的localhost地址------------

http_url=""

""" 
首先，你有一个有公网ip地址的服务器

然后，使用nginx
sudo apt update
sudo apt install nginx

启动
sudo service nginx start
or
sudo systemctl start nginx

设置开机自启动
sudo update-rc.d nginx defaults


sudo vim /etc/nginx/sites-available/default
在 /etc/nginx/sites-available/default 文件中，找到 server 块并添加以下内容：
server {
    listen 80;
    server_name 123.45.67.89;  # 使用你的公网IP地址，或者localhost

    location /images/ {
        alias /root/autodl-tmp/images/;  #这里是你的图片本地文件根目录
    }

    # 其他配置...
}


确保没有语法错误
sudo nginx -t

重启服务
sudo service nginx restart

#----权限配置，如果位于工作目录下----------
sudo chown -R www-data:www-data /root/autodl-tmp/images/ #递归更改所有文件的所有者为www-data，/root/autodl-tmp/images/是你的图片本地文件根目录

#www-data用户是nginx的默认运行的组和用户，需要所有父目录的读取权限，建议重新创建一个根目录存储图片

sudo chmod -R 755 /root/autodl-tmp/images/
sudo  chmod -R 755 /root/autodl-tmp/
sudo chmod -R 755 /root/
#设置权限为755，以便www-data用户可以访问

#如果可以，建议重新创建/var/www/imags目录与root分离，将图片迁移到/var/www/imags目录下，并设置权限为755。
#var权限为drwxr-xr-x，一般来说，其他用户有读和执行的权限 
sudo chmod -R 755 /var/www/
sudo chmod -R 755 /var/www/imags/


这里假设 nginx 运行的用户是 www-data。如果你的用户不同，请根据实际情况调整。

默认使用端口80

访问测试：
http://123.45.67.89/images/xxxxxxx.jpg

如果可以正常访问，说明nginx配置成功。
80端口直接使用http访问
"""






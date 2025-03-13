ATS RESUME SCORER 

The main logic used for this is in the file resume.py 

the other two folders are essentially the backend(django) and the frontend(react) of a website that would be an ats scorer 

I am currently in the process of launching it as a website, just looking into how i should launch it, and working on the style and especially on some new features to be added. 

for now this is how it works, we got the main directory on the ubuntu (after setting up the vm of course), then routed the django file to gunicorn, and then gunicorn to nginx

http://13.39.135.220 here is the public ip if u wanna access it 

finally added style, was a bit of a hastle with the nginx routing but it ended up working

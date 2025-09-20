# Configuratitons
First we have to create a server using ngrok(free) and add the link to the Twilio Sandbox , to do this follow the steps given below.
# ngrok
First install ngrok.
Then run "ngrok http 5000"
Now you will see a website like " https://some-random-characters.ngrok-free.app "
Copy the link that you see
# Twilio Configuration 
In The Twilio Website(https://console.twilio.com/) ,
Log into the website(and set up your account) and open the messaging tab on the left.
Then go to try it out and click on Send a Whatsapp Message and click on Sandbox Settings
Then on "WHEN A MESSAGE COMES IN" , set the link to the link you got + "/webhook"
So the link should be of form:
https://some-random-characters.ngrok-free.app/webhook
Make sure the Method is on POST and click on SAVE.
# env file
Make sure to save your GOOGLE_API in the .env file as
GOOGLE_API_KEY="your_key"
# AI Features and Drawbacks
This AI can be configured to different modes by typing the word "configure" .
There are 4 Modes : Tutor, Buddy, Explaination , Normal
This AI has memory in it and can hold upto 5 interactions of memory.
I could have implemented Images and Audio if i had more time but i ran out of free use of gemini and Twilio before that point
I Could also host this on a render.com server , but due to the lack of time , i was not able to do so.
import re, json, os, urllib2
import pandas as pd
from textblob import TextBlob
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf 
from gi.repository import Gio 

class TApp (object):

        def __init__(self):
                self.builder = Gtk.Builder()
                self.builder.add_from_file("gui.glade")
                self.builder.connect_signals(self)

        def run(self):
                self.builder.get_object("login_window").show_all()
                Gtk.main()

        def quit_app(self, *args):
                Gtk.main_quit()
        
        def login_btn_clicked_cb(self, *args):
                username = self.builder.get_object('username').get_text()
                password = self.builder.get_object('password').get_text()
                if (username == 'admin' and password == 'password'):
                        self.builder.get_object("main_window").show_all()
                        self.builder.get_object("login_window").hide()
                
        def fd_show(self, *args):
                self.builder.get_object("fd_window").show_all()
        
        def fd_close(self, *args):
                self.builder.get_object("fd_window").hide()
        
        def fd2_show(self, *args):
                self.builder.get_object("fd2_window").show_all()

        def load_feelings(self, *args):
                self.feeling_list = self.builder.get_object('feeling_list')
                self.mapfeeling={}
                fdir = self.builder.get_object("fd_window").get_filename()
                if fdir:
                        self.fd_close()
                        for line in open(fdir, 'r').readlines():
                                line = line.strip().split(':')
                                self.feeling_list.append([line[0].strip(), line[1], False])
                                self.mapfeeling[line[0].strip()]=0
                self.builder.get_object("button2").set_sensitive(True)
                self.builder.get_object("button2").set_label("Analyse tweets")
                # Text analysis function
        def feeling(self, text):
                output = []
                for feeling, words, enabled in self.feeling_list: # Loop throught feelings
                        # if enabled == True:
                        for word in words.split(','): # Loop through words
                                msg = TextBlob(text)
                                if word in msg.words: # Check if the word exists in text
                                        output.append(feeling)
                return ', '.join(output) if output else "unknown"

        # Calculate the message's sentiment
        def sentiment(self, text):
                msg = TextBlob(text)
                return msg.sentiment.polarity

        # Text cleanup function
        def cleanup(self,  text):
                text = re.sub(r'(?:^|\s)(\#\w+)', '', text) # Remove hashtags
                text = re.sub(r'(?:^|\s)(\@\w+)', '', text) # Remove at (@)
                text = text.encode('ascii',errors='ignore')
                text = text.rstrip()
                return text # Return the cleaned up text

        def load_tweets(self, *args):
                print("Load Tweets")
                self.tweets_list = self.builder.get_object('tweets_list')
                tweets_data = [] # Create a list which will contain all the tweets
                tweets = pd.DataFrame(columns=['username', 'text', 'country', 'feeling', 'sentiment']) # Create a panda table
                fdir = self.builder.get_object("fd2_window").get_filename()

                for line in open(fdir,"r").readlines(): # Iterate over each line inside the input file
                        try:
                                tweet = json.loads(line) # Load the line content into json
                                if 'text' in tweet: # Check if the tweet has any content
                                        tweets_data.append(tweet) # Add the tweet to the tweets_data list
                        except:
                                continue

                feelingtoken=0
                idnum=0
                for feel in self.mapfeeling :
                        if self.mapfeeling[feel]==1:
                                feelingtoken=1
                                break
                                
                # Load all of the content into a panda table
                tweets['username'] = map(lambda tweet: tweet['user']['screen_name'] if 'user' in tweet else 'none', tweets_data)
                tweets['country'] = map(lambda tweet: tweet['user']['location'] if 'user' in tweet else 'none', tweets_data)
                tweets['image'] = map(lambda tweet: tweet['user']['profile_image_url'] if 'user' in tweet else 'none', tweets_data)
                tweets['text'] = map(lambda tweet: self.cleanup(tweet['text']) if 'text' in tweet else 'none', tweets_data)
                tweets['feeling'] = map(lambda tweet: self.feeling(self.cleanup(tweet['text'].lower())) if 'text' in tweet else 'unknown', tweets_data)
                tweets['sentiment'] = map(lambda tweet: self.sentiment(self.cleanup(tweet['text'].lower())) if 'text' in tweet else 'unknown', tweets_data)

                for i, data in tweets.iterrows():
                        try:
                                res = urllib2.urlopen(data['image'])
                        except:
                                res = urllib2.urlopen("http://a0.twimg.com/sticky/default_profile_images/default_profile_6_normal.png")
                        input_stream = Gio.MemoryInputStream.new_from_data(res.read(), None) 
                        pixbuf = Pixbuf.new_from_stream(input_stream, None) 
                        markup = '<a href="http://twitter.com/%s">Link</a>'%data['username']
                        feeling=data['feeling']
                        if data['feeling'] == 'unknown':
                                feeling=''
                                
                        country=data['country']
                        if data['country'] == 'unknown':
                                country=''
                                
                        if feelingtoken==0:
                                self.tweets_list.append([str(idnum), data['username'], pixbuf, data['text'], country, feeling, str(data['sentiment'])])
                                idnum+=1
                        else:
                                if feeling!='':
                                        restrip = feeling.strip().split(',')
                                        flag=0
                                        for i in range(len(restrip)):
                                                if self.mapfeeling[restrip[i].strip()]==1:
                                                        flag=1
                                                        break
                                        if flag==1:
                                                self.tweets_list.append([str(idnum), data['username'], pixbuf, data['text'], country, feeling, str(data['sentiment'])])
                                                idnum+=1
                                
                                
                self.builder.get_object("fd2_window").hide()
                self.builder.get_object("button2").set_sensitive(False)
                self.builder.get_object("button2").set_label("Done")

        def t_toggle(self, widget, path):
                self.mapfeeling[self.feeling_list[path][0]]=self.mapfeeling[self.feeling_list[path][0]]^1
                self.feeling_list[path][2] = not self.feeling_list[path][2]
                
        def text_changed(self, widget, path, text):
                self.feeling_list[path][1] = text
        
        def reset(self, *args):
                self.builder.get_object('tweets_list').clear()
                self.builder.get_object('feeling_list').clear()
                self.builder.get_object("button2").set_label("Load feelings first")
        def row_clicked(self, treeview, path, view_column):
                import webbrowser
                username =  self.tweets_list[path][1]
                webbrowser.open("http://twitter.com/%s"%username)
TApp().run()

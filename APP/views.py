from django.http import HttpResponse, HttpResponseRedirect,JsonResponse
from sklearn.feature_extraction.text import CountVectorizer
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize,sent_tokenize
from django.shortcuts import render,redirect
from googletrans import Translator
from django.conf import settings
from nltk.corpus import wordnet
from nltk.tag import pos_tag
from .models import *
import dns.resolver
import requests
import joblib
import socket
import aiml
import nltk 
import os
import re

nltk.download('vader_lexicon')
urdu_pattern = r'^[\u0600-\u06FF\s]+$'
translator = Translator()

def init_kernel():
    kernel = aiml.Kernel()
    kernel.bootstrap(learnFiles=os.path.abspath("Data/aiml/*.aiml"))
    return kernel
krnl = init_kernel()


def ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_address = s.getsockname()[0]
    s.close()
    return ip_address


def obj_relate(text):
    tokens = word_tokenize(text)
    tagged_tokens = pos_tag(tokens)
    nouns = [word for word, pos in tagged_tokens if pos.startswith('NN')]
    verbs = [word for word, pos in tagged_tokens if pos.startswith('VB')]
    noun_str = ", ".join(nouns)
    verb_str = ", ".join(verbs)
    return noun_str, verb_str


def define_word(word):
    synsets = wordnet.synsets(word)
    a = "No definitions found."
    if synsets:
        definition = synsets[0].definition()
        return definition
    else:
        return a


def mood(request):
    name = request.session.get('name')
    sia = SentimentIntensityAnalyzer()

    user_msg = User_msg.nodes.filter(name=name).first()
    if user_msg is None or not user_msg.chat:
        sentiment = 'neutral'
    else:
        sentiment_list = []
        for message in user_msg.chat:
            scores = sia.polarity_scores(message)

            if scores['compound'] >= 0.05:
                sentiment = 'positive'
            elif scores['compound'] <= -0.05:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

            sentiment_list.append(sentiment)

    return sentiment

def link_user_chat(request,n):
    chat = User_msg(name=n, name_node="User_Chat").save()
    user = Register.nodes.get(username=n)
    user.res.connect(chat)


def user_chat(request, message):
    name = request.session.get('name')
    chat_store_node = User_msg.nodes.filter(name=name).first()
    if chat_store_node:
        chat_store_node.save_message(message)
    else:
        chat_store_node = User_Chat(email=user_mail2, name="Chats")
        chat_store_node.save_message(message)


def predict_gender(name):
    model = joblib.load(os.path.abspath("Data/ml/gender_detect.pkl"))
    vectorizer = CountVectorizer()
    vocabulary = joblib.load(os.path.abspath("Data/ml/vocabulary.pkl"))
    vectorizer.vocabulary_ = vocabulary
    
    name_vectorized = vectorizer.transform([name])
    predicted_gender = model.predict(name_vectorized)[0]
    return predicted_gender


def home(request):
    return render(request, 'index.html')


def register_view(request):
    if request.method == 'POST':
        n = request.POST['username']
        m = request.POST['email']
        sp = request.POST['password']
        try:
            tell = Register.nodes.get(username=n)
            return render(request, 'dup_name.html')
        except Register.DoesNotExist:
            g = predict_gender(n)
            Register(username=n, email=m, password=sp, ip=ip(),gender = g).save()
            request.session['mail'] = m
            request.session['name'] = n
            link_user_chat(request, n)
            return redirect('home')
    
    return render(request, 'register.html')


def login(request):
    if request.method == 'POST':
        Q = request.POST['username']
        P = request.POST['Password']
        try:
            user = Register.nodes.get(username=Q, password=P)
            return redirect('home')
        except:
             return render(request, 'e_p_chk.html')
    return render(request, 'login.html')


def chat(request):
    name = request.session.get('name')
    mail = request.session.get('mail')
    krnl.setPredicate('name', name.capitalize())
    krnl.setPredicate('m', mail)
    a = predict_gender(name)
    krnl.setPredicate('gender', a)
    bot_name = "Sara"
    krnl.setPredicate('master',bot_name)
    ip1 = ip()
    krnl.setPredicate('ip', ip1)
    mo = mood(request)
    krnl.setPredicate('mood', mo)
    if request.method == 'POST':
        user_message = request.POST['message']

        if  re.match(urdu_pattern, user_message):
            english = translator.translate(user_message).text
            response = krnl.respond(english)
            bot_response = translator.translate(response, dest='ur').text
            return JsonResponse({'bot_response': bot_response})

        elif "have" in user_message.lower() or "have a" in user_message.lower() or "have another" in user_message.lower():
            nouns, verbs = obj_relate(user_message)
            node1 = Thing(username=name, thing_name=nouns).save()
            user = Register.nodes.get(username=name)
            user.th.connect(node1)
            bot_response = krnl.respond(user_message)
            user_chat(request,user_message)
            return JsonResponse({'bot_response': bot_response})
        elif "is my" in user_message or "of mine" in user_message:
            user_chat(request, user_message)
            bot_response = krnl.respond(user_message)
            s = Register.nodes.get(username=name)
            words = user_message.split()
            first_word = words[0]
            word = words[-1]
            q = word.upper()
            if q == "FATHER":
                a = predict_gender(first_word)
                f = Friend(name = name,F_name = first_word,gender=a).save()
                s.j.connect(f)
                return JsonResponse({'bot_response': bot_response})
            elif q == "MOTHER":
                a = predict_gender(first_word)
                f = Friend(name = name,F_name = first_word,gender=a).save()
                s.k.connect(f)
                return JsonResponse({'bot_response': bot_response})
            elif q == "FRIEND":
                a = predict_gender(first_word)
                f = Friend(name = name,F_name = first_word,gender=a).save()
                s.i.connect(f)
                return JsonResponse({'bot_response': bot_response})
            elif q == "SISTER" or q == "SIS":
                a = predict_gender(first_word)
                f = Friend(name = name,F_name = first_word,gender=a).save()
                s.m.connect(f)
                return JsonResponse({'bot_response': bot_response})
            elif q == "BROTHER" or q == "BRO":
                a = predict_gender(first_word)
                f = Friend(name = name,F_name = first_word,gender=a).save()
                s.n.connect(f)
                return JsonResponse({'bot_response': bot_response})
            else:
                bot_response = krnl.respond(user_message)
                return JsonResponse({'bot_response': bot_response})
        elif "Define" in user_message.capitalize():
            bot_response = define_word(user_message)
            if bot_response == "No definitions found.":
                bot_response = krnl.respond(user_message)
                return JsonResponse({'bot_response': bot_response})
            else: 
                return JsonResponse({'bot_response': bot_response})
        else:
            user_chat(request, user_message)
            bot_response = krnl.respond(user_message)
            if bot_response == "I'm sorry, I didn't understand what you said.":
                bot_response = get_completion(user_message)
                return JsonResponse({'bot_response': bot_response})
            else:
                return JsonResponse({'bot_response': bot_response})
    return render(request, 'chat.html')

def get_completion(message):
    url = "https://free.churchless.tech/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": message}]}
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    if 'choices' in data and len(data['choices']) > 0:
        completion = data['choices'][0]['message']['content']
        return completion.strip()
    return "I'm sorry, I didn't understand what you said."
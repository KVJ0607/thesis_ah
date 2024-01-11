
#from sentiment.sentiment import *

import csv 
from utils.constant import ZH_DICTIONARY,EN_DICTIONARY,ZH_STOPWORDS,EN_STOPWORDS
def cal_tone_score():
    pass

def making_a_dictionary():
    resulting_dict={}
    with open('data/vsa/正面情感词语(中文)_encoded.txt', 'r', encoding='utf-8') as file:
        # Read each line in the file one by one
        for line in file:
            # The line variable contains each line as a string
            word_=line.strip()  # strip() removes leading/trailing whitespace, including newlines
            resulting_dict[word_]={'positive':1,'negative':0}
    with open('data/vsa/正面评价词语(中文)_encoded.txt', 'r', encoding='utf-8') as file:
        # Read each line in the file one by one
        for line in file:
            # The line variable contains each line as a string
            word_=line.strip()  # strip() removes leading/trailing whitespace, including newlines
            resulting_dict[word_]={'positive':1,'negative':0}            
            
    with open('data/vsa/负面情感词语(中文)_encoded.txt', 'r', encoding='utf-8') as file:
        # Read each line in the file one by one
        for line in file:
            # The line variable contains each line as a string
            word_=line.strip()  # strip() removes leading/trailing whitespace, including newlines
            resulting_dict[word_]={'positive':0,'negative':1}    

    with open('data/vsa/负面评价词语(中文)_encoded.txt', 'r', encoding='utf-8') as file:
        # Read each line in the file one by one
        for line in file:
            # The line variable contains each line as a string
            word_=line.strip()  # strip() removes leading/trailing whitespace, including newlines
            resulting_dict[word_]={'positive':0,'negative':1}    
    return resulting_dict

def save_dict_to_csv(dictionary, csv_file_path=ZH_DICTIONARY):
    with open(csv_file_path, mode='w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write the header
        writer.writerow(['word', 'positive', 'negative'])
        # Write the dictionary content
        for word, flags in dictionary.items():
            writer.writerow([word, flags['positive'], flags['negative']])

def load_dict_from_csv(csv_file_path=ZH_DICTIONARY):
    with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        retrieved_dict = {}
        for row in reader:
            # Convert the flags back to integers
            retrieved_dict[row['word']] = {'positive': int(row['positive']), 'negative': int(row['negative'])}
        return retrieved_dict


def making_a_dictionary_eng():
    resulting_dict={}
    with open('data/vsa/正面情感词语(英文)_encoded.txt', 'r', encoding='utf-8') as file:
        # Read each line in the file one by one
        for line in file:
            # The line variable contains each line as a string
            word_=line.strip()  # strip() removes leading/trailing whitespace, including newlines
            resulting_dict[word_]={'positive':1,'negative':0}
    with open('data/vsa/正面评价词语(英文)_encoded.txt', 'r', encoding='utf-8') as file:
        # Read each line in the file one by one
        for line in file:
            # The line variable contains each line as a string
            word_=line.strip()  # strip() removes leading/trailing whitespace, including newlines
            resulting_dict[word_]={'positive':1,'negative':0}            
            
    with open('data/vsa/负面情感词语(英文)_encoded.txt', 'r', encoding='utf-8') as file:
        # Read each line in the file one by one
        for line in file:
            # The line variable contains each line as a string
            word_=line.strip()  # strip() removes leading/trailing whitespace, including newlines
            resulting_dict[word_]={'positive':0,'negative':1}    

    with open('data/vsa/负面评价词语(英文)_encoded.txt', 'r', encoding='utf-8') as file:
        # Read each line in the file one by one
        for line in file:
            # The line variable contains each line as a string
            word_=line.strip()  # strip() removes leading/trailing whitespace, including newlines
            resulting_dict[word_]={'positive':0,'negative':1}    
    return resulting_dict


def save_dict_to_csv_eng(dictionary, csv_file_path=EN_DICTIONARY):
    with open(csv_file_path, mode='w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write the header
        writer.writerow(['word', 'positive', 'negative'])
        # Write the dictionary content
        for word, flags in dictionary.items():
            writer.writerow([word, flags['positive'], flags['negative']])

def load_dict_from_csv_eng(csv_file_path=EN_DICTIONARY):
    with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        retrieved_dict = {}
        for row in reader:
            # Convert the flags back to integers
            retrieved_dict[row['word']] = {'positive': int(row['positive']), 'negative': int(row['negative'])}
        return retrieved_dict


def load_stopwords(file_path=ZH_STOPWORDS):
    with open(file_path, 'r', encoding='utf-8') as file:
        stopwords = set(line.strip() for line in file if line.strip())
    return stopwords

def load_stopwords_en(file_path=EN_STOPWORDS):
    with open(file_path, 'r', encoding='utf-8') as file:
        stopwords = set(line.strip() for line in file if line.strip())
    return stopwords
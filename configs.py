import io 
import re 
import pandas as pd
import json
from datetime import datetime

def read_txt(path):
  file = io.open(path, mode='r', encoding='utf-8')
  result = file.read()
  return result

def read_json(path):
  with open(path, mode='r' , encoding='utf-8') as json_file:
    result = json.load(json_file)
  return result

def shingle(ls, num):
  result = []
  for i in range(len(ls) - num + 1):
    result.append(' '.join(ls[i:i + num]))
  return result

def stopwords_sorting(stopwords):
  stw_df = pd.DataFrame(stopwords, columns=['stw'])
  stw_df['len'] = stw_df['stw'].str.len()
  stw_df = stw_df.sort_values(by=['len'], ascending=False)
  stw_ls = stw_df['stw'].tolist()
  return stw_ls

# def text_format(text, stopwords):
#   processed_text = re.sub(r'\s+', ' ', text)
#   processed_text = re.sub(r'\Whttp[s]?:\S+|\Ahttp[s]?:\S+', '|', processed_text)
#   processed_text = re.sub(r'_x\d+d_', '|', processed_text)
#   processed_text = re.sub(r'\d+', '|', processed_text)
#   processed_text = re.sub(r'_', '|', processed_text)
#   processed_text = re.sub(r'[^\w\s]', '|', processed_text)

#   for stw in stopwords:
#     processed_text = re.sub(f'\W{stw}\W|\A{stw}\W|\W{stw}\Z|\A{stw}\Z', ' | ', processed_text)

#   processed_text = re.sub(r'\|+', '|', re.sub(r'[\s]?\|[\s]?', '|', processed_text))

#   return processed_text

def text_format(text, stopwords):
  ls = [x for x in re.split(r' |_', text) if x != '']

  final = []

  for i in range(len(ls)):
    final.append('|' if (re.match(r'http[s]?:\S+', ls[i]) or re.findall(r'\d', ls[i]) or re.match(r'\W+', ls[i])) else ls[i])

  processed_text = ' '.join(final)
  for stw in stopwords:
    processed_text = re.sub(f'\W{stw}\W|\A{stw}\W|\W{stw}\Z|\A{stw}\Z', ' | ', processed_text)

  processed_text = re.sub(r'\|+', '|', re.sub(r'[\s]?\|[\s]?', '|', processed_text))

  return processed_text

def doc_format(doc, stopwords):
  result = []
  for conv in doc:
    conv_format = text_format(conv, stopwords).strip('|').split('|')
    result.append(conv_format)
  return result

def bundle_listing(conv_ls):
  bundle_ls = []
  for conv in conv_ls:
    for sen in conv:
      word_ls = sen.split()
      for i in range(4):
        i += 1
        bundle_ls.extend(shingle(word_ls, i))
  return bundle_ls

def bundle_counting(bundle_ls):
  bundle_count = {}
  for bundle in bundle_ls:
    if bundle not in bundle_count.keys():
      bundle_count[bundle] = 0
    bundle_count[bundle] += 1
  return bundle_count

def first_bundle(bundle_count, bundle_level):
  first_bundle = {}
  for bundle in bundle_count.keys():
    key = ' '.join(bundle.split()[:bundle_level])
    if key not in first_bundle.keys():
      first_bundle[key] = {}
      first_bundle[key]['total'] = 0
      first_bundle[key]['main'] = 0
      first_bundle[key]['children'] = {}
    
    first_bundle[key]['total'] += bundle_count[bundle]
    if key == bundle:
      first_bundle[key]['main'] += bundle_count[bundle]
    else:
      first_bundle[key]['children'][bundle] = bundle_count[bundle]

  return first_bundle

def last_bundle(bundle_count, bundle_level):
  last_bundle = {}
  for bundle in bundle_count.keys():
    key = ' '.join(bundle.split()[-bundle_level:])
    if key not in last_bundle.keys():
      last_bundle[key] = {}
      last_bundle[key]['total'] = 0
      last_bundle[key]['main'] = 0
      last_bundle[key]['children'] = {}
    
    last_bundle[key]['total'] += bundle_count[bundle]
    if key == bundle:
      last_bundle[key]['main'] += bundle_count[bundle]
    else:
      last_bundle[key]['children'][bundle] = bundle_count[bundle]

  return last_bundle

def first_bundle_all_level(bundles):
  for w1 in bundles.keys():
    w1_children = first_bundle(bundles[w1]['children'], 2)

    for w2 in w1_children.keys():
      w2_children = first_bundle(w1_children[w2]['children'], 3)
      w1_children[w2]['children'] = w2_children

    bundles[w1]['children'] = w1_children
  return bundles

def last_bundle_all_level(bundles):
  for w1 in bundles.keys():
    w1_children = last_bundle(bundles[w1]['children'], 2)

    for w2 in w1_children.keys():
      w2_children = last_bundle(w1_children[w2]['children'], 3)
      w1_children[w2]['children'] = w2_children

    bundles[w1]['children'] = w1_children
  return bundles

def bundle_score(bundles, threshold):
  bundle_score = {}
  for w1 in bundles.keys():
    w1_total = bundles[w1]['total']
    w1_main = bundles[w1]['main']
    w1_children = bundles[w1]['children']

    f2_neg = 0
    f2_f3 = 0
    f2_f4 = 0
    for w2 in w1_children.keys():
      w2_total = w1_children[w2]['total']
      w2_main = w1_children[w2]['main']
      w2_children = w1_children[w2]['children']

      f3_neg = 0
      f3_f4 = 0
      for w3 in w2_children.keys():
        w3_total = w2_children[w3]['total']
        w3_main = w2_children[w3]['main']
        w3_children = w2_children[w3]['children']
        
        f4_neg = 0
        for w4 in w3_children.keys():
          w4_total = w3_children[w4]
          w4_main = w3_children[w4]
          f4 = w4_total / w1_total

          if f4 > threshold:
            if w4 not in bundle_score.keys():
              bundle_score[w4] = {}
            bundle_score[w4]['count'] = w4_total
            bundle_score[w4]['pct'] = f4
            f4_neg += f4

        f3 = (w3_total / w1_total) - f4_neg
        if f3 > threshold:
          if w3 not in bundle_score.keys():
            bundle_score[w3] = {}
          bundle_score[w3]['count'] = w3_total
          bundle_score[w3]['pct'] = f3
          f3_neg += f3
        f3_f4 += f4_neg
      
      f2 = (w2_total / w1_total) - f3_neg - f3_f4
      if f2 > threshold:
        if w2 not in bundle_score.keys():
          bundle_score[w2] = {}
        bundle_score[w2]['count'] = w2_total
        bundle_score[w2]['pct'] = f2
        f2_neg += f2
      f2_f3 += f3_neg
      f2_f4 += f3_f4

    f1 = 1 - f2_neg - f2_f3 - f2_f4
    if f1 > threshold:
      if w1 not in bundle_score.keys():
        bundle_score[w1] = {}
      bundle_score[w1]['count'] = w1_total
      bundle_score[w1]['pct'] = f1
  return bundle_score

def tokenizer(conv_ls, token_ls):
  f_tokens_dict = {}
  l_tokens_dict = {}
  for token in token_ls:
    m = str(token).split()
    xf = m[0]
    xl = m[-1]
    y = len(m)
    
    if xf not in f_tokens_dict.keys():
      f_tokens_dict[xf] = {1: [], 2: [], 3: [], 4: []}
    f_tokens_dict[xf][y].append(token)
    
    if xl not in l_tokens_dict.keys():
      l_tokens_dict[xl] = {1: [], 2: [], 3: [], 4: []}
    l_tokens_dict[xl][y].append(token)
        
  final = {}
  for index in range(len(conv_ls)):
    ls = conv_ls[index]
    
    f_result = []
    for s in ls:
      w = s.split()
      for i in range(len(w)):
        z = 1
        d = {}
        for j in [4, 3, 2, 1]:
          # b = tokens_dict[w[i]][j]
          if w[i] in f_tokens_dict.keys():
            b = f_tokens_dict[w[i]][j]
            if len(b)> 0:
              for k in b:
                if str(s).find(str(k)) >= 0:
                  d[z] = k 
                  z = 0
          else:
            d[z] = w[i]
        if 1 in d.keys():
          f_result.append(d[1])
    
    l_result = []
    for s in ls:
      w = s.split()
      for i in range(len(w)):
        z = 1
        d = {}
        for j in [4, 3, 2, 1]:
          # b = tokens_dict[w[i]][j]
          if w[i] in l_tokens_dict.keys():
            b = l_tokens_dict[w[i]][j]
            if len(b)> 0:
              for k in b:
                if str(s).find(str(k)) >= 0:
                  d[z] = k 
                  z = 0
          else:
            d[z] = w[i]
        if 1 in d.keys():
          l_result.append(d[1])

    result = [x for x in f_result if x in l_result]
    
    final[index] = result
  return final

def fl_tokenizer(doc, stopwords_ls, threshold):
  stopwords = stopwords_sorting(stopwords_ls)
  formatted_conv_ls = doc_format(doc, stopwords) 

  bundle_ls = bundle_listing(formatted_conv_ls)

  bundle_count = bundle_counting(bundle_ls)

  first_bundles = first_bundle_all_level(first_bundle(bundle_count, 1))
  last_bundles = last_bundle_all_level(last_bundle(bundle_count, 1))

  first_bundle_sc = bundle_score(first_bundles, threshold)
  last_bundle_sc = bundle_score(last_bundles, threshold)

  first_tokens = list(first_bundle_sc.keys())
  last_tokens = list(last_bundle_sc.keys())

  tokens = [token for token in first_tokens if token in last_tokens]

  final = tokenizer(formatted_conv_ls, tokens)

  final_ls = list(final.values())

  return final_ls
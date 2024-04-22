import io
import re
import json

def read_file(path, file_type='txt'):
  with io.open(path, mode='r', encoding='utf-8') as file:
    if file_type == 'json':
      return json.load(file)
    else:
      return file.read()

def shingle(ls, num):
  return [' '.join(ls[i:i + num]) for i in range(len(ls) - num + 1)]

def stopwords_sorting(stopwords):
  return sorted(stopwords, key=len, reverse=True)

def text_format(text, stopwords):
  words = re.split(r'[\s_]+', text)
  processed_text = ' '.join('|' if (re.match(r'http[s]?:\S+', word) or re.findall(r'\d', word) or re.match(r'\W+', word)) else word for word in words)
  for stw in stopwords:
      processed_text = re.sub(rf'\b{stw}\b', '|', processed_text)
  return re.sub(r'\|+', '|', processed_text).strip('|')

def doc_format(doc, stopwords):
  return [text_format(conv, stopwords).split('|') for conv in doc]

def bundle_listing(conv_ls):
  bundle_ls = []
  for conv in conv_ls:
    for sen in conv:
      word_ls = sen.split()
      for i in range(4):
        i += 1
        bundle_ls.extend(shingle(word_ls, i))
  return bundle_ls
  # return [shingle(sen.split(), i) for conv in conv_ls for sen in conv for i in range(1, 5)]

def bundle_counting(bundle_ls):
  bundle_count = {}
  for bundle in bundle_ls:
    bundle_count[bundle] = bundle_count.get(bundle, 0) + 1
  return bundle_count

def bundle_structure(bundle_count, bundle_level, position='first'):
  bundles = {}
  for bundle, count in bundle_count.items():
    key = ' '.join(bundle.split()[:bundle_level] if position == 'first' else bundle.split()[-bundle_level:])
    if key not in bundles:
      bundles[key] = {'total': 0, 'main': 0, 'children': {}}
    bundles[key]['total'] += count
    if key == bundle:
      bundles[key]['main'] += count
    else:
      bundles[key]['children'][bundle] = count
  return bundles

def recursive_bundle_structure(bundles, level=2, position='first'):
  for key, value in bundles.items():
    if value['children']:
      value['children'] = bundle_structure(value['children'], level, position)
      recursive_bundle_structure(value['children'], level + 1, position)
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
          w4_total = w3_children[w4]['total']
          w4_main = w3_children[w4]['main']
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

  first_bundles = recursive_bundle_structure(bundle_structure(bundle_count, 1, 'first'), position='first')
  last_bundles = recursive_bundle_structure(bundle_structure(bundle_count, 1, 'last'), position='last')

  first_bundle_sc = bundle_score(first_bundles, threshold)
  last_bundle_sc = bundle_score(last_bundles, threshold)

  first_tokens = list(first_bundle_sc.keys())
  last_tokens = list(last_bundle_sc.keys())

  tokens = [token for token in first_tokens if token in last_tokens]

  final = tokenizer(formatted_conv_ls, tokens)

  final_ls = list(final.values())

  return final_ls
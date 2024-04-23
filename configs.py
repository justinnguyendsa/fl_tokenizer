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
  words = re.split(r'[\s_]+', text.lower())
  processed_text = ' '.join('|' if (re.match(r'http[s]?:\S+', word) or re.findall(r'\d', word) or re.match(r'\W+', word)) else word for word in words)
  processed_text = re.sub(r'[^\w\s]', '|', processed_text)
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
  for w1, w1_data in bundles.items():
    w1_total = w1_data['total']
    w1_children = w1_data['children']

    f2_neg, f2_f3, f2_f4 = 0, 0, 0
    for w2, w2_data in w1_children.items():
      w2_total = w2_data['total']
      w2_children = w2_data['children']

      f3_neg, f3_f4 = 0, 0
      for w3, w3_data in w2_children.items():
        w3_total = w3_data['total']
        w3_children = w3_data['children']

        f4_neg = 0
        for w4, w4_data in w3_children.items():
          w4_total = w4_data['total']

          f4 = w4_total / w1_total
          if f4 > threshold:
            bundle_score.setdefault(w4, {'count': w4_total, 'pct': f4})
            f4_neg += f4

        f3 = (w3_total / w1_total) - f4_neg
        if f3 > threshold:
          bundle_score.setdefault(w3, {'count': w3_total, 'pct': f3})
          f3_neg += f3
        f3_f4 += f4_neg

      f2 = (w2_total / w1_total) - f3_neg - f3_f4
      if f2 > threshold:
        bundle_score.setdefault(w2, {'count': w2_total, 'pct': f2})
        f2_neg += f2
      f2_f3 += f3_neg
      f2_f4 += f3_f4

    f1 = 1 - f2_neg - f2_f3 - f2_f4
    if f1 > threshold:
      bundle_score.setdefault(w1, {'count': w1_total, 'pct': f1})

  return bundle_score

def tokenizer(conv_ls, token_ls):
  f_tokens_dict = {}
  l_tokens_dict = {}
  for token in token_ls:
    m = token.split()
    xf, xl = m[0], m[-1]
    y = len(m)
    
    f_tokens_dict.setdefault(xf, {1: [], 2: [], 3: [], 4: []})[y].append(token)
    l_tokens_dict.setdefault(xl, {1: [], 2: [], 3: [], 4: []})[y].append(token)
  
  final = {}
  for index, ls in enumerate(conv_ls):
    f_result = []
    l_result = []
    for s in ls:
      words = s.split()
      for i, word in enumerate(words):
        f, l = 0, 0
        for j in range(4, 0, -1):
          for token in f_tokens_dict.get(word, {}).get(j, []):
            if f != 0:
              break
            elif token in s:
              f_result.append(token)
              f = 1
              break
          for token in l_tokens_dict.get(word, {}).get(j, []):
            if l != 0:
              break
            elif token in s:
              l_result.append(token)
              l = 1
              break

    final[index] = [x for x in f_result if x in l_result]

  return final

def fl_tokenizer(doc, stopwords_ls, threshold=0.01):
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
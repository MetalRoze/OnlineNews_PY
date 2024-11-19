import networkx
import re
# 텍스트 전처리용 stop_words 목록
# stop_words = set([
#     '>','<'
#     '의', '가', '이', '은', '는', '을', '를', '에', '에서', '으로', '로', '과', '와', '한', '하다', '들', '되다', '이다',
#     '그', '그것', '저', '저것', '수', '되다', '것', '좀', '잘', '많이', '그럼', '그리고', '하지만', '왜', '어떤', '누구', '무엇', '<p>', '<br>', '</p>'
# ])
class RawSentence:
    def __init__(self, textIter):
        if type(textIter) == str: self.textIter = textIter.split('\n')
        else: self.textIter = textIter
        self.rgxSplitter = re.compile('([.!?:](?:["\']|(?![0-9])))')
 
    def __iter__(self):
        for line in self.textIter:
            ch = self.rgxSplitter.split(line)
            for s in map(lambda a, b: a + b, ch[::2], ch[1::2]):
                if not s: continue
                yield s
 
class RawSentenceReader:
    def __init__(self, filepath):
        self.filepath = filepath
        self.rgxSplitter = re.compile('([.!?:](?:["\']|(?![0-9])))')
 
    def __iter__(self):
        for line in open(self.filepath, encoding='utf-8'):
            ch = self.rgxSplitter.split(line)
            for s in map(lambda a, b: a + b, ch[::2], ch[1::2]):
                if not s: continue
                yield s
 
class RawTagger:
    def __init__(self, textIter, tagger = None):
        if tagger:
            self.tagger = tagger
        else :
            from konlpy.tag import Komoran
            self.tagger = Komoran()
        if type(textIter) == str: self.textIter = textIter.split('\n')
        else: self.textIter = textIter
        self.rgxSplitter = re.compile('([.!?:](?:["\']|(?![0-9])))')
 
    def __iter__(self):
        for line in self.textIter:
            ch = self.rgxSplitter.split(line)
            for s in map(lambda a,b:a+b, ch[::2], ch[1::2]):
                if not s: continue
                yield self.tagger.pos(s)
 
class RawTaggerReader:
    def __init__(self, filepath, tagger = None):
        if tagger:
            self.tagger = tagger
        else :
            from konlpy.tag import Komoran
            self.tagger = Komoran()
        self.filepath = filepath
        self.rgxSplitter = re.compile('([.!?:](?:["\']|(?![0-9])))')
 
    def __iter__(self):
        for line in open(self.filepath, encoding='utf-8'):
            ch = self.rgxSplitter.split(line)
            for s in map(lambda a,b:a+b, ch[::2], ch[1::2]):
                if not s: continue
                yield self.tagger.pos(s)
 
class TextRank:
    def __init__(self, **kargs):
        self.graph = None
        self.window = kargs.get('window', 5)
        self.coef = kargs.get('coef', 1.0)
        self.threshold = kargs.get('threshold', 0.005)
        self.dictCount = {}
        self.dictBiCount = {}
        self.dictNear = {}
        self.nTotal = 0
 
 
    def load(self, sentenceIter, wordFilter = None):
        def insertPair(a, b):
            if a > b: a, b = b, a
            elif a == b: return
            self.dictBiCount[a, b] = self.dictBiCount.get((a, b), 0) + 1
 
        def insertNearPair(a, b):
            self.dictNear[a, b] = self.dictNear.get((a, b), 0) + 1
 
        for sent in sentenceIter:
            for i, word in enumerate(sent):
                if wordFilter and not wordFilter(word): continue
                self.dictCount[word] = self.dictCount.get(word, 0) + 1
                self.nTotal += 1
                if i - 1 >= 0 and (not wordFilter or wordFilter(sent[i-1])): insertNearPair(sent[i-1], word)
                if i + 1 < len(sent) and (not wordFilter or wordFilter(sent[i+1])): insertNearPair(word, sent[i+1])
                for j in range(i+1, min(i+self.window+1, len(sent))):
                    if wordFilter and not wordFilter(sent[j]): continue
                    if sent[j] != word: insertPair(word, sent[j])
 
    def loadSents(self, sentenceIter, tokenizer = None):
        import math
        def similarity(a, b):
            n = len(a.intersection(b))
            return n / float(len(a) + len(b) - n) / (math.log(len(a)+1) * math.log(len(b)+1))
 
        if not tokenizer: rgxSplitter = re.compile('[\\s.,:;-?!()"\']+')
        sentSet = []
        for sent in filter(None, sentenceIter):
            if type(sent) == str:
                if tokenizer: s = set(filter(None, tokenizer(sent)))
                else: s = set(filter(None, rgxSplitter.split(sent)))
            else: s = set(sent)
            if len(s) < 2: continue
            self.dictCount[len(self.dictCount)] = sent
            sentSet.append(s)
 
        for i in range(len(self.dictCount)):
            for j in range(i+1, len(self.dictCount)):
                s = similarity(sentSet[i], sentSet[j])
                if s < self.threshold: continue
                self.dictBiCount[i, j] = s
 
    def getPMI(self, a, b):
        import math
        co = self.dictNear.get((a, b), 0)
        if not co: return None
        return math.log(float(co) * self.nTotal / self.dictCount[a] / self.dictCount[b])
 
    def getI(self, a):
        import math
        if a not in self.dictCount: return None
        return math.log(self.nTotal / self.dictCount[a])
 
    def build(self):
        self.graph = networkx.Graph()
        self.graph.add_nodes_from(self.dictCount.keys())
        for (a, b), n in self.dictBiCount.items():
            self.graph.add_edge(a, b, weight=n*self.coef + (1-self.coef))
 
    def rank(self):
        return networkx.pagerank(self.graph, weight='weight')
 
    def extract(self, ratio=0.1):
        ranks = self.rank()
        cand = sorted(ranks, key=ranks.get, reverse=True)[:int(len(ranks) * ratio)]
        keywords = []  # keywords 리스트 초기화

        for k in cand:
            # 한국어 명사(NNG, NNP)와 영어 단어도 모두 처리하도록 변경
            if k[1] == 'NNG' or k[1] == 'NNP' or k[1] == 'NN' or k[1] == 'VB':  # 'NN'과 'VB'는 영어 명사와 동사 태그
                keywords.append(k[0])  # 단어를 keywords 리스트에 추가

        # 필터링된 keywords 리스트 반환
        return keywords
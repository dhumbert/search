import math
import functools
import itertools
import string
from bs4 import BeautifulSoup
from customtypes import OrderedSet


class Document:
    def __init__(self, doc_id, title, body):
        self.id = doc_id
        self.title = title
        self.body = body

    def __repr__(self):
        return '<Document {}: {}>'.format(self.id, self.title)

    def to_dict(self):
        return {
            'title': self.title,
            'body': self.body,
        }


class Parser:
    def docs(self):
        raise NotImplementedError()


class ReutersArchiveParser(Parser):
    def __init__(self, file_to_read):
        self.body = BeautifulSoup(file_to_read.read())

    def docs(self):
        for article in self.body.find_all('reuters'):
            title = article.title.text if article.title else ''
            if article.body:
                yield Document(article['newid'], title,
                               article.body.text)

    def find_by_id(self, doc_id):
        article = self.body.find('reuters', newid=doc_id)

        title = article.title.text if article.title else ''

        if article.body:
            return Document(article['newid'], title,
                            article.body.text)


def _build_term_frequencies():
    terms = {}
    num_articles = 0

    with open('../reuters21578/reut2-000.sgm') as sgml_file:
        parser = ReutersArchiveParser(sgml_file)

        for doc in parser.docs():
            num_articles += 1

            terms[doc.id] = {}
            article_terms = terms[doc.id]

            for word in map(lambda x: x.lower(), doc.body.split()):
                while word and word[-1] in string.punctuation:
                    word = word[0:-1]

                if word:
                    while word and word[0] in string.punctuation:
                        word = word[1:]

                    if word[-2:] == "'s":
                        word = word[0:-2]

                    if word not in article_terms:
                        article_terms[word] = 0

                    article_terms[word] += 1
    return terms, num_articles


def build_index():
    terms, num_articles = _build_term_frequencies()

    all_term_freqs = {}

    all_terms = sorted(
        itertools.chain.from_iterable([x.items() for x in terms.values()]),
        key=lambda x: x[0])

    for k, g in itertools.groupby(all_terms, lambda x: x[0]):
        all_term_freqs[k] = len(list(g))  # num of documents the term appears in

    idx = {}
    for doc_id, doc_terms in terms.items():
        for term, freq in doc_terms.items():
            idf = math.log(num_articles / (1 + all_term_freqs[term]))
            tfidf = freq * idf

            if term not in idx:
                idx[term] = []

            idx[term].append((tfidf, doc_id,))

    for term in idx:
        idx[term] = sorted(idx[term], key=lambda x: x[0], reverse=True)

    return idx


def search(query, idx):
    query_terms = query.split()
    term_sets = []
    for term in query_terms:
        if term in idx:
            docs = OrderedSet(x[1] for x in idx[term])
            term_sets.append(docs)

    if term_sets:
        doc_intersections = functools.reduce(lambda s1, s2: s1 & s2, term_sets)

        if doc_intersections:
            with open('../reuters21578/reut2-000.sgm') as file_to_read:
                parser = ReutersArchiveParser(file_to_read)
                for doc_id in doc_intersections:
                    yield parser.find_by_id(doc_id)

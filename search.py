import re
import readline
from urllib.parse import urlparse, parse_qs
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from colorama import init as colorama_init, Fore
from tfidf import build_index, search


def search_cli():
    idx = build_index()
    colorama_init()

    while True:
        query = input('query> ')

        results = search(query, idx)
        if results:
            pattern = re.compile(r'(' + '|'.join(map(lambda x: r'\b{}\b'.format(x), query.split())) + ')', re.IGNORECASE)

            for result in results:
                print(result.title)

                article_text = result.body.strip()
                article_text = pattern.sub(Fore.RED + r'\1' + Fore.RESET, article_text)

                print(article_text)
                print('===================================================')
        else:
            print('No Results.')


def search_server():
    idx = build_index()
    class SearchRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            qs = parse_qs(urlparse(self.path).query)

            if 'q' in qs:
                query = qs['q'][0]
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                results = list(map(lambda x: x.to_dict(), search(query, idx)))
                self.wfile.write(json.dumps(results, ensure_ascii=False).encode('utf8'))
                return
            else:
                self.send_response(400, "Bad Request")
                self.end_headers()
                return

    server = HTTPServer(("", 8000), SearchRequestHandler)
    server.serve_forever()


if __name__ == '__main__':
    search_server()
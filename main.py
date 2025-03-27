import math
from fastapi import FastAPI, UploadFile, File, HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")


class WordCounter:
    def __init__(self, words):
        self.word_dict = {}
        self._count_words(words)

    def _count_words(self, words):
        for word in words:
            if word in self.word_dict:
                self.word_dict[word] += 1
            else:
                self.word_dict[word] = 1

    def items(self):
        return self.word_dict.items()


results_storage = []

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request, page: int = 1, per_page: int = 50):
    global results_storage

    if not results_storage:
        return templates.TemplateResponse(
            "index.html",
            {"request": request}
        )

    total_items = len(results_storage)
    total_pages = math.ceil(total_items / per_page)
    start = (page - 1) * per_page
    end = min(start + per_page, total_items)
    paginated_results = results_storage[start:end]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "results": paginated_results,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "total_items": total_items
        }
    )


@app.post("/", response_class=HTMLResponse)
async def root(
        request: Request,
        file: UploadFile = File(...),
        page: int = 1,
        per_page: int = 20
    ):
    try:
        global results_storage

        content = await file.read()
        text = content.decode('utf-8').lower()

        words = text.split()
        word_counts = WordCounter(words)
        total_words = len(words)
        tf_scores = {word: count / total_words for word, count in word_counts.items()}

        idf_scores = {word: math.log(1 + total_words / (1 + count))
                      for word, count in word_counts.items()}


        results_storage = [(word, tf_scores[word], idf_scores[word])
                   for word in word_counts.word_dict]
        results_storage.sort(key=lambda x: x[2], reverse=True)

        total_items = len(results_storage)
        total_pages = math.ceil(total_items / per_page)
        start = (page - 1) * per_page
        end = min(start + per_page, total_items)
        paginated_results = results_storage[start:end]

        print(page)

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "results": paginated_results,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "total_items": total_items
            }
        )
    except UnicodeEncodeError:
        raise HTTPException(status_code=400, detail="Invalid text file format")
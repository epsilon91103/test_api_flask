# -*- coding: utf-8 -*-

import json
import datetime

import flask
from flask_sqlalchemy import SQLAlchemy

# список полей, которые может указывать пользователь
ARTICLE_INPUT_FIELDS = ['author', 'content']

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///articles.sqlite3'

db = SQLAlchemy(app)


class Article(db.Model):
    id = db.Column('article_id', db.Integer, primary_key=True)
    author = db.Column(db.String(100))
    content = db.Column(db.Text(4000))
    created = db.Column(db.DateTime, default=datetime.datetime.now())
    updated = db.Column(db.DateTime, default=datetime.datetime.now())

    def __init__(self, author, content):
        self.author = author
        self.content = content

    def __repr__(self):
        return "<Article({}, {})>".format(self.id, self.author)

    # обновление атрибутов
    def updated_info(self, author=None, content=None):
        """Attribute update"""
        if author is not None:
            self.author = author
        if content is not None:
            self.content = content

        self.updated = datetime.datetime.now()

    # возврат информации об объекте в виде словаря
    def get_info(self):
        """Return information about the object in the form of a dictionary"""

        info = {
                "id": self.id,
                "author": self.author,
                "content": self.content,
                "created": self.created.strftime('%Y-%m-%dT%H:%M:%S'),
                "updated": self.updated.strftime('%Y-%m-%dT%H:%M:%S')
        }

        return info


# возврат объекта по id
def get_by_id(art_id):
    """Return object by id"""
    return db.session.query(Article).filter(Article.id == art_id).first()


def resp(code, data):
    return flask.Response(
        status=code,
        mimetype="application/json",
        response=json.dumps(data)
    )


# проверка json на корректность
def article_validate(all_fields=True):
    """Json check for correctness"""
    error = []

    article_info = flask.request.get_json()

    if article_info is None or not article_info:
        error.append("No JSON sent")
        return None, error

    for field_name in ARTICLE_INPUT_FIELDS:
        if field_name not in article_info:
            if all_fields:
                error.append("Field '{}' not specified".format(field_name))
            else:
                article_info[field_name] = None
        else:
            if type(article_info[field_name]) is not str:
                error.append("Field '{}' is missing or is not a string".format(field_name))

    return article_info, error


# возврат ошибки при отсутствии объекта
def err_not_found_obj(art_id):
    """Error return with no object"""
    return 404, {"error": 'article {} not found'.format(art_id)}


# обновление аттрибутов объекта
def update_article(article_id, article_update_info, errors):
    """Updating object attributes"""
    if errors:
        return 400, {"errors": errors}
    else:
        article = get_by_id(article_id)

        if article is None:
            return err_not_found_obj(article_id)
        else:
            article.updated_info(
                article_update_info['author'],
                article_update_info['content']
            )
            db.session.commit()

            return 200, article.get_info()


@app.route('/')
def root():
    return flask.redirect('/api/articles')


@app.route('/api/articles', methods=['GET'])
def get_articles():
    articles = [article.get_info() for article in db.session.query(Article).all()]
    return resp(200, {"objects": articles})


@app.route('/api/articles/<int:article_id>', methods=['GET'])
def get_article(article_id):
    article = get_by_id(article_id)

    if article is None:
        return resp(*err_not_found_obj(article_id))
    else:
        return resp(200, article.get_info())


@app.route('/api/articles', methods=['POST'])
def post_article():
    (article_info, errors) = article_validate()

    if errors:
        return resp(400, {"errors": errors})
    else:
        article = Article(article_info['author'], article_info['content'])

        db.session.add(article)
        db.session.commit()

        return resp(200, article.get_info())


@app.route('/api/articles/<int:article_id>', methods=['PUT'])
def put_article(article_id):
    (article_info, errors) = article_validate()
    return resp(*update_article(article_id, article_info, errors))


@app.route('/api/articles/<int:article_id>', methods=['PATCH'])
def patch_article(article_id):
    (article_info, errors) = article_validate(all_fields=False)
    return resp(*update_article(article_id, article_info, errors))


@app.route('/api/articles/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    article = get_by_id(article_id)

    if article is None:
        return resp(*err_not_found_obj(article_id))
    else:
        db.session.delete(article)
        db.session.commit()

        return resp(200, {"message": 'ok'})


if __name__ == '__main__':
    db.create_all()
    app.run(debug=False)

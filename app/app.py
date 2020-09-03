from json.decoder import JSONDecodeError

from flask import Flask, render_template, request

from constructor.main import MetaClass

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    classname = request.form.get('classname') or ''
    jsondata = request.form.get('jsondata') or ''
    metaclass = None
    errors = {}
    if classname and jsondata:
        try:
            metaclass = MetaClass.from_json(classname, jsondata)
        except JSONDecodeError as e:
            errors['JSONDecodeError'] = e
        except NotImplementedError as e:
            errors['NotImplementedError'] = e
    return render_template('index.html',
                           classname=classname,
                           jsondata=jsondata,
                           metaclass=metaclass,
                           errors=errors)


if __name__ == '__main__':
    app.run()

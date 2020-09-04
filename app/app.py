from json.decoder import JSONDecodeError

from flask import Flask, render_template, request

from constructor.main import MetaClass
from constructor.utils import cleanup

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        classname = request.form.get('classname') or ''
        jsondata = request.form.get('jsondata') or ''
        skip_fields_with_errors = bool(request.form.get('skipFieldsWithErrors'))
        print(request.form)
        metaclass = None
        errors = {}
        if classname and jsondata:
            try:
                metaclass = MetaClass.from_json(classname, jsondata, skip_fields_with_errors)
            except JSONDecodeError as e:
                errors['JSONDecodeError'] = e
            except NotImplementedError as e:
                errors['NotImplementedError'] = e
        rendered = render_template('index.html',
                                   classname=classname,
                                   jsondata=jsondata,
                                   metaclass=metaclass,
                                   errors=errors,
                                   skip_fields_with_errors=skip_fields_with_errors)
        return rendered
    finally:
        cleanup()


if __name__ == '__main__':
    app.run()

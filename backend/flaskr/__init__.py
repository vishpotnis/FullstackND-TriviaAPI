from flask import Flask, request, abort, jsonify
from flask_cors import CORS
from sqlalchemy.sql.expression import func

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
  Set up CORS. Allow '*' for origins.
  '''
    CORS(app)

    '''
  Use the after_request decorator to set Access-Control-Allow
  '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization')
        response.headers.add('Access-Control.Allow-Methods',
                             'GET, POST PATCH, DELETE, OPTIONS')

        return response

    '''
  an endpoint to handle GET requests
  for all available categories.
  '''
    @app.route('/categories')
    def get_categories():
        return jsonify({
            'success':  True,
            'categories': {category.id: category.type
                           for category in Category.query.all()}
        })

    '''
  endpoint to handle GET requests for questions,
  including pagination (every 10 questions).
  This endpoint should return a list of questions,
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom
  of the screen for three pages.
  Clicking on the page numbers should update the questions.
  '''

    def paginate_questions(request, selection):
        page = request.args.get('page', 1, type=int)
        start = (page-1) * QUESTIONS_PER_PAGE
        stop = start + QUESTIONS_PER_PAGE

        questions = [question.format() for question in selection]
        current_questions = questions[start:stop]

        return current_questions

    @app.route('/questions')
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions':  current_questions,
            'total_questions': len(selection),
            'categories': [category.type for category in Category.query.all()],
            'current_category': []
        })

    '''
  endpoint to DELETE question using a question ID.

  TEST: When you click the trash icon next to a question,
  the question will be removed.
  This removal will persist in the database and when you refresh the page.
  '''
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question_by_id(question_id):

        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            print(question)

            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': question_id,
            })

        except Exception:
            abort(422)

    '''
  an endpoint to POST a new question,
  which will require the question and answer text,
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab,
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  '''
    '''
  POST endpoint to get questions based on a search term.
  It should return any questions for whom the search term
  is a substring of the question.

  TEST: Search by any phrase. The questions list will update to include
  only question that include that string within their question.
  Try using the word "title" to start.
  '''

    @app.route('/questions', methods=['POST'])
    def add_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)
        search_term = body.get('searchTerm', None)

        if search_term:

            selection = Question.query.filter(
                Question.question.ilike(f'%{search_term}%')).all()
            current_questions = paginate_questions(request, selection)

            if len(selection) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(selection),
                'current_category': []
            })

        else:

            try:
                question = Question(question=new_question,
                                    answer=new_answer,
                                    category=new_category,
                                    difficulty=new_difficulty)
                question.insert()

                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'questions':  current_questions,
                    'total_questions': len(selection),
                })

            except Exception:
                abort(422)

    '''
  GET endpoint to get questions based on category.

  TEST: In the "List" tab / main screen, clicking on one of the
  categories in the left column will cause only questions of that
  category to be shown.
  '''
    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        current_category = Category.query.filter(
            Category.id == category_id).first()

        selection = Question.query.order_by(Question.id).filter(
            Question.category == str(category_id)).all()
        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions':  current_questions,
            'total_questions': len(selection),
            'categories': [category.type for category in Category.query.all()],
            'current_category': current_category.format()
        })

    '''
  a POST endpoint to get questions to play the quiz.
  This endpoint should take category and previous question parameters
  and return a random questions within the given category,
  if provided, and that is not one of the previous questions.

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not.
  '''
    @app.route('/quizzes', methods=['POST'])
    def get_quiz_questions():

        try:
            body = request.get_json()

            quiz_category = body.get('quiz_category', None)
            previous_questions = body.get('previous_questions', None)

            category_id = int(quiz_category['id'])

            if category_id == 0:
                question = Question.query.filter(~Question.id.in_(
                    previous_questions)).order_by(func.random()).first()
            else:
                question = Question.query.filter(Question.category ==
                                                 category_id).filter(
                        ~Question.id.in_(previous_questions)).order_by(
                            func.random()).first()

            return jsonify({
                'success':  True,
                'question': question.format() if question else None
            })
        except Exception:
            abort(422)

    '''
  error handlers for all expected errors
  including 404 and 422.
  '''
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    return app

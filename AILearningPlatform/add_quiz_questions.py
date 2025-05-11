"""Script to add sample quiz questions for each course."""
from app import create_app
from extensions import db
from models import Course, QuizQuestion

def add_sample_questions():
    app = create_app()
    
    with app.app_context():
        # Get all courses
        courses = Course.query.all()
        
        # Sample questions for different subjects
        questions_data = {
            'Data Science': [
                {
                    'question': 'What is the primary purpose of data cleaning in data science?',
                    'options': [
                        'To make data look pretty',
                        'To remove or correct corrupt, incomplete, or irrelevant data',
                        'To convert all data to text format',
                        'To compress data for storage'
                    ],
                    'answer': 'To remove or correct corrupt, incomplete, or irrelevant data'
                },
                {
                    'question': 'Which of the following is NOT a common data science programming language?',
                    'options': [
                        'Python',
                        'R',
                        'Java',
                        'SQL'
                    ],
                    'answer': 'Java'
                }
            ],
            'Machine Learning': [
                {
                    'question': 'What is the difference between supervised and unsupervised learning?',
                    'options': [
                        'Supervised learning uses labeled data, unsupervised uses unlabeled data',
                        'Supervised learning is faster than unsupervised learning',
                        'Unsupervised learning requires human intervention',
                        'There is no difference'
                    ],
                    'answer': 'Supervised learning uses labeled data, unsupervised uses unlabeled data'
                },
                {
                    'question': 'What is overfitting in machine learning?',
                    'options': [
                        'When a model is too simple',
                        'When a model captures noise in the training data',
                        'When a model is trained for too few epochs',
                        'When a model uses too many features'
                    ],
                    'answer': 'When a model captures noise in the training data'
                }
            ],
            'Artificial Intelligence': [
                {
                    'question': 'What is the Turing Test used for?',
                    'options': [
                        'To test computer processing speed',
                        'To determine if a machine can exhibit intelligent behavior',
                        'To measure AI algorithm efficiency',
                        'To evaluate computer memory capacity'
                    ],
                    'answer': 'To determine if a machine can exhibit intelligent behavior'
                },
                {
                    'question': 'Which of the following is NOT a subset of AI?',
                    'options': [
                        'Machine Learning',
                        'Deep Learning',
                        'Neural Networks',
                        'Data Mining'
                    ],
                    'answer': 'Data Mining'
                }
            ]
        }
        
        # Add questions to each course
        for course in courses:
            # Use course title to get relevant questions
            course_questions = questions_data.get(course.title, [])
            
            # If no specific questions for this course, use a default set
            if not course_questions:
                course_questions = [
                    {
                        'question': f'What is the main topic of the course "{course.title}"?',
                        'options': [
                            course.title,
                            'A different topic',
                            'Not related to the course',
                            'General knowledge'
                        ],
                        'answer': course.title
                    },
                    {
                        'question': f'Which of the following is a key concept in {course.title}?',
                        'options': [
                            'Basic arithmetic',
                            'Advanced concepts',
                            'Foundational principles',
                            'All of the above'
                        ],
                        'answer': 'All of the above'
                    }
                ]
            
            # Add questions to the course
            for q in course_questions:
                question = QuizQuestion(
                    course_id=course.id,
                    question=q['question'],
                    options=q['options'],
                    correct_answer=q['answer']
                )
                db.session.add(question)
        
        # Commit all changes
        db.session.commit()
        print(f"Added quiz questions for {len(courses)} courses.")

if __name__ == "__main__":
    add_sample_questions()

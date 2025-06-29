from src.routes.care_info_routes import care_info_routes
from src.routes.fitness_routes import fitness_routes
from src.routes.other_routes import other_routes
from src.routes.user_routes import user_routes
from src.routes.dog_routes import dog_routes
from src.routes.collar_routes import collar_routes
from src.routes.faq_routes import faq_routes
from src.routes.nutrition_routes import nutrition_routes
from src.routes.vaccinations_routes import vaccinations_routes
from src.routes.medical_records_routes import medical_records_routes
from src.routes.places_routes import places_routes
from src.routes.goals_routes import goals_routes
from src.routes.activities_routes import activities_routes
from src.routes.favorite_places_routes import favorite_places_routes
from src.routes.friends_routes import friends_routes


def init_routes(app):
    app.register_blueprint(user_routes)
    app.register_blueprint(dog_routes)
    app.register_blueprint(collar_routes)
    app.register_blueprint(other_routes)
    app.register_blueprint(fitness_routes)
    app.register_blueprint(care_info_routes)
    app.register_blueprint(faq_routes)
    app.register_blueprint(nutrition_routes)
    app.register_blueprint(vaccinations_routes)
    app.register_blueprint(medical_records_routes)
    app.register_blueprint(places_routes)
    app.register_blueprint(goals_routes)
    app.register_blueprint(activities_routes)
    app.register_blueprint(favorite_places_routes)
    app.register_blueprint(friends_routes)

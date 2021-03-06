from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.weather.weatherfactory import WeatherFactory
from .forms import TourForm, SearchTourForm, DelayTourForm
from ..db.tourmanager import TourDAO
from app.db.usermanager import UserDAO
from app.db.registrationmanager import RegistrationDAO
from app.db.notificationmanager import NotificationDAO

import time
from datetime import datetime

tours_blueprint = Blueprint('tours', __name__)
tours_blueprint.current_items_per_page = None
tours_blueprint.current_order_by = None


@tours_blueprint.route('/tours')
def tours_default():
    return redirect(url_for('.tours', current_page=1))


@tours_blueprint.route('/tours/<int:current_page>', methods=('GET', 'POST'))
def tours(current_page):
    tour_form = TourForm()

    if not tours_blueprint.current_items_per_page:
        tours_blueprint.current_items_per_page = \
            tour_form.tours_per_page.default

    if not tours_blueprint.current_order_by:
        tours_blueprint.current_order_by = tour_form.order_by.default

    if tour_form.validate_on_submit():
        tours_blueprint.current_items_per_page = tour_form.tours_per_page.data
        tours_blueprint.current_order_by = tour_form.order_by.data
        return redirect(url_for('tours.tours_default'))

    pagination = TourDAO.get_page_of_tours(
        current_page, tours_blueprint.current_items_per_page,
        tours_blueprint.current_order_by
    )

    app_tours = []
    if current_user.is_authenticated:
        rows = RegistrationDAO.get_registrations_tour_ids_of_user(current_user)
        app_tours = [x[0] for x in rows]

    return render_template('tours.html',
                           tour_form=tour_form,
                           tours=pagination.items, pagination=pagination,
                           items=tours_blueprint.current_items_per_page,
                           sort=tours_blueprint.current_order_by,
                           apply_tours=app_tours)


@tours_blueprint.route('/view-tour/<int:tour_id>')
def view_tour(tour_id):
    tour = TourDAO.get_tour_by_id(tour_id)
    weathers = WeatherFactory(tour.place, 7).get_weathers()
    
    applyed = False
    if current_user.is_authenticated:
        applyed = RegistrationDAO.check_registrated(current_user, tour)

    delay = DelayTourForm()

    return render_template('tour-view.html',
                           tour=tour,
                           weathers=weathers, user=current_user, applyed=applyed)


@tours_blueprint.route('/search-tours', methods=('GET', 'POST'))
def search_tours():
    tour_search_form = SearchTourForm()

    if tour_search_form.validate_on_submit():

        place = tour_search_form.place.data
        date = tour_search_form.date.data

        results = []

        if place and date:
            results = TourDAO.get_list_of_tours_by_place_and_date(
                place, date)
        elif place:
            results = TourDAO.get_list_of_tours_by_place(place)
        elif date:
            results = TourDAO.get_list_of_tours_by_date(date)

        if results:
            return render_template('tour-search.html',
                                   tour_search_form=tour_search_form,
                                   results=results)

    return render_template('tour-search.html',
                           tour_search_form=tour_search_form,
                           results=None)


@tours_blueprint.route('/update-tour-images/<int:id_>/<string>')
@login_required
def update_tour_images(id_, string):
    if current_user.account_type_id == 1:
        TourDAO.update_images(TourDAO.get_tour_by_id(id_), string)
        return '1'
    else:
        return u'Hozzáférés megtagadva'

@tours_blueprint.route('/deleteTour/<int:id>')
@login_required
def deleteTour(id):
    tourname = TourDAO.getNameOfTour(id)
    print(tourname)
    listOfIds = TourDAO.delete_tour(id)

    message = "Kedves Felhasználó!\n Sajnálatos módon a " +  tourname + "túrát le kell mondanunk. \n Köszönjük megértésed. \n(Az 5 tura utáni kedvezmény természetesen megmarad.)" 

    NotificationDAO.insert_new_message(listOfIds, "Túra törlés", message)

    return redirect(url_for('.tours', current_page=1))    

@tours_blueprint.route('/tourdelay/<int:id>/<string:date>')
@login_required
def tourdelay(id, date):
    tourname = TourDAO.getNameOfTour(id)
    dateval = datetime.strptime(date, '%Y.%m.%d. %H:%M')
    
    if dateval < datetime.now():
        return '0'

    TourDAO.delay_tour(id, dateval, tourname)

    return '1'
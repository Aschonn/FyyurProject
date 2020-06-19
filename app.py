# ---------------------------------------------------------------------------#
# Imports
# ---------------------------------------------------------------------------#

import dateutil.parser
import babel
from sqlalchemy import func
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
import json

# ---------------------------------------------------------------------------#
# App Config.
# ---------------------------------------------------------------------------#

# TODO: connect to a local postgresql database: done in config.py

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# ---------------------------------------------------------------------------#
# Attach Migrate Class
# ---------------------------------------------------------------------------#
migrate = Migrate(app, db)


# ---------------------------------------------------------------------------#
# Models.
# ---------------------------------------------------------------------------#


from models import *


# ---------------------------------------------------------------------------#
# Filters.
# ---------------------------------------------------------------------------#
def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format="EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format="EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  #acquire all venues
  venues = Venue.query.all()
  #if no venues display error

  data = []
  #iterate through all venues
  for venue in venues:
    
    #open slot
    venue_data = []
    
    #get the state and city from venue
    area_venues = Venue.query.filter_by(state=venue.state).filter_by(city=venue.city).all()
    
    #get venue id from shows 
    shows = Show.query.filter_by(venue_id=venue.id).all()
    
    #get current time
    current_date = datetime.now()
    
    #starter for num of upcoming shows
    num_upcoming_shows = 0

    #adds to num_upcoming_shows if there are upcoming shows
    for show in shows:
      if show.start_time > current_date:
        num_upcoming_shows += 1

    for area in area_venues:
      venue_data.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming_shows
        })

    data.append({
      "city": area.city,
      "state": area.state, 
      "venues": venue_data
    })


  return render_template('pages/venues.html', areas = data)
  
  #                   Visuals:
  
  # city  
  # state
  # Venue
  #     id
  #     name
  #     upcoming shows



#  SEARCH POST
#  ----------------------------------------------------------------

@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  #grab user input`
  search_term = request.form.get('search_term', '')
  #search through all venue names and make a list of matching results
  search_result = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
  data = []

  for result in search_result:
    data.append({
      "id": result.id,
      "name": result.name,
      #get number of shows from filtering out the queries with same id 
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.artist_id == result.id).filter(Show.start_time > datetime.now()).all()),
    })
  #if any results show it will display number of results and data associated to it
  response={
    "count": len(search_result),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

#  SHOW VENUE
#  ----------------------------------------------------------------

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  
  venue = Venue.query.get(venue_id)

  #filter out the shows that have same id and havent happened
  matching = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id)

  #get upcoming and past show list
  upcoming_shows_maybe = matching.filter(Show.start_time>datetime.now()).all()
  past_shows_maybe = matching.filter(Show.start_time<datetime.now()).all()


  upcoming_shows = []
  past_shows = []

  #iterate through
  for show in past_shows_maybe:
    past_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  #iterate through
  for show in upcoming_shows_maybe:
    upcoming_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")    
    })

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_venue.html', venue=data)


#  Get A Create Venue Form
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

#  Submit A Create Venue Form
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  
  try:
    #gets all user inputs
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website = request.form['website']
    seeking_talent = request.form['seeking_talent']
    seeking_description = request.form['seeking_description']
  
  #creates new venue
    venue = Venue(
      name=name, 
      city=city, 
      state=state, 
      address=address, 
      phone=phone, 
      genres=genres, 
      facebook_link=facebook_link, 
      image_link=image_link, 
      website=website, 
      seeking_talent=seeking_talent, 
      seeking_description=seeking_description
      )

    db.session.add(venue)
    db.session.commit()
    flash('Congrats the venue was listed!')
  except: 
    db.session.rollback()
    flash('Oh No! Something wrong. The venue was not be listed.', sys.exc_info())
  finally: 
    db.session.close()
  
  
  return render_template('pages/home.html')


#  DELETE VENUE
#  ----------------------------------------------------------------

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  
  try:
    #get venue ID then session delete
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Congrats the venue ' + request.form['name'] + ' was successfully deleted!')
  except:
    db.session.rollback()
    flash('Oh No! Something wrong. The venue' + request.form['name']+ ' could not be listed.', sys.exc_info())
  finally:
    db.session.close()
  return render_template('pages/home.html')



#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = db.session.query(Artist).all()
  return render_template('pages/artists.html', artists=data)


#  Artist Search
#  ----------------------------------------------------------------


@app.route('/artists/search', methods=['POST'])
def search_artists():
  #get input search
  search_term = request.form.get('search_term', '')
  
  #compare input search and all artists extracts matching
  search_items = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
  
  #open slot
  data = []
  #iterate through Items and make those categories accessable
  for item in search_items:
    data.append({
      "id": result.id,
      "name": item.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.artist_id == item.id).filter(Show.start_time > datetime.now()).all()),
    })
  
  response = {
    "count": len(search_items),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term = request.form.get('search_term', ''))



#  Show Artists
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  get_artist_maybe = db.session.query(Artist).get(artist_id)

  if get_artist_maybe:

    #join models and get matching id
    matching = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id)
    
    #get past shows
    past_shows_maybe = matching.filter(Show.start_time>datetime.now()).all()
    
    #get upcoming shows
    upcoming_shows_maybe = matching.filter(Show.start_time>datetime.now()).all()
    
    
    #open slot
    past_shows = []
    upcoming_shows = []

    for show in past_shows_maybe:
      past_shows.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })
  

    for show in upcoming_shows_maybe:
      upcoming_shows.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })


    data = {
      "id": get_artist_maybe.id,
      "name": get_artist_maybe.name,
      "genres": get_artist_maybe.genres,
      "city": get_artist_maybe.city,
      "state": get_artist_maybe.state,
      "phone": get_artist_maybe.phone,
      "website": get_artist_maybe.website,
      "facebook_link": get_artist_maybe.facebook_link,
      "seeking_venue": get_artist_maybe.seeking_venue,
      "seeking_description": get_artist_maybe.seeking_description,
      "image_link": get_artist_maybe.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_artist.html', artist=data)



#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  #get form
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  #if true update values
  if artist: 
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website.data = artist.website
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)


#  Edit Artist
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id): 
  
  artist = Artist.query.get(artist_id)

  try: 
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website']
    artist.seeking_venue = ['seeking_venue']
    artist.seeking_description = request.form['seeking_description']

    db.session.commit()
    flash('Congrats the venue ' + request.form['name'] + ' was successfully deleted!')
  except: 
    db.session.rollback()
    flash('Oh No! Something wrong. The venue' + request.form['name']+ ' could not be listed.', sys.exc_info())
  finally: 
    db.session.close()


  return redirect(url_for('show_artist', artist_id=artist_id))

      


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  if venue: 
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.address.data = venue.address
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website.data = venue.website
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=venue)


#  Edit Venue
#  ----------------------------------------------------------------

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  #get specific venue
  venue = Venue.query.get(venue_id)

  try: 
    #get user inputs and replace old values with new
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website']
    venue.seeking_talent = True if 'seeking_talent' in request.form else False 
    venue.seeking_description = request.form['seeking_description']
    #commit changes
    db.session.commit()
    flash('Congrats the venue update was a success!')
  except: 
    db.session.rollback()
    flash(f'An error occurred. Venue could not be changed.', sys.exc_info())
  finally: 
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))


  

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  
  try: 
    #get user inputs
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres'),
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website = request.form['website']
    artist.seeking_venue = ['seeking_venue']
    seeking_description = request.form['seeking_description']
    
    #create new artist
    artist = Artist(
      name=name, 
      city=city, 
      state=state, 
      phone=phone, 
      genres=genres, 
      facebook_link=facebook_link, 
      image_link=image_link, website=website, 
      seeking_venue=seeking_venue, 
      seeking_description=seeking_description
      )


    db.session.add(artist)
    db.session.commit()
    flash('Artist was listing was a successfully!')
  except: 
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name']+ ' could not be listed.')
  finally: 
    db.session.close()
    
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  #join all the models to display correct info to html page
  shows = db.session.query(Show).join(Artist).join(Venue).all()
  #open slot
  data = []
  #iterate through all values and append it to data to make it accessable
  for show in shows: 
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name, 
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  return render_template('pages/shows.html', shows=data)


#  Show Create Form
#  ----------------------------------------------------------------


@app.route('/shows/create')
def create_shows():

  form = ShowForm()
  return render_template('forms/new_show.html', form=form)




#  Create Shows
#  ----------------------------------------------------------------



@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  try: 
    #grab user input
    artist = request.form['artist_id']
    venue = request.form['venue_id']
    start_time = request.form['start_time']
    #create new show
    show = Show(artist_id=artist, venue_id=venue, start_time=start_time)
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed')
  except: 
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
    print(sys.exc_info())
  finally: 
    db.session.close()
    
  return render_template('pages/home.html')
    

#  Error Messages
#  ----------------------------------------------------------------

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


# ---------------------------------------------------------------------------#
# Launch.
# ---------------------------------------------------------------------------#


# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
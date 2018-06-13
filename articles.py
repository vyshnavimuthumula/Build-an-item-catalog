from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Company, Base, Article, User

engine = create_engine('sqlite:///watches.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()
User1 = User(name="vyshnavi", email="vyshnavi.muthumula@gmail.com")
session.add(User1)
session.commit()


company1 = Company(user_id=1, name="Titan")
session.add(company1)
session.commit()
article1 = Article(user_id=1, name="Analog", description="ladies watch",
                   price="$60", type="belt", company=company1)

session.add(article1)
session.commit()

article2 = Article(user_id=1, name="Digital", description="boys watches",
                   type="chain", price="$80", company=company1)

session.add(article2)
session.commit()

article3 = Article(user_id=1, name="Chronograph",
                   description="stop watch combined with a display watch",
                   type="metal", price="$20", company=company1)

session.add(article3)
session.commit()

company2 = Company(user_id=1, name="Breguet")
session.add(company2)
session.commit()

article1 = Article(user_id=1, name="Swiss watch",
                   description="Swiss watch industry is stronger than ever",
                   price="$35", type="belt", company=company2)

session.add(article1)
session.commit()

article2 = Article(user_id=1, name="Sports watch",
                   description="Sports watches are not just timing races ",
                   price="$60", type="chain", company=company2)

session.add(article2)
session.commit()

article3 = Article(user_id=1, name="Space watch",
                   description="Worn by astronauts in outer space",
                   price="$65", type="metal", company=company2)

session.add(article3)
session.commit()
# Bracelets
company3 = Company(user_id=1, name="AQUA APATITE/ BRASS.")
session.add(company3)
session.commit()

article1 = Article(user_id=1, name="Bangle bracelet",
                   description=" Kind of ring with no opening at all",
                   price="$50", type="silver",  company=company3)

session.add(article1)
session.commit()

article2 = Article(user_id=1, name="Cuff bracelet",
                   description="Very similar to the bangle bracelet",
                   price="$55", type="gold", company=company3)

session.add(article2)
session.commit()

article3 = Article(user_id=1, name="Charm bracelet",
                   description="Charm bracelets are another kind of bracelets",
                   price="$35", type="platinum",  company=company3)

session.add(article3)
session.commit()

print("Article details are added!")

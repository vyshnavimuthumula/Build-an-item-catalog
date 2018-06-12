# Build-an-item-catalog
####Project Overview
To Develop an application that provides a list of products within a variety of types as well as provide a user registration and authentication system. Registered users will have the ability to create, edit and delete their own products.

####Why This Project?
Modern web applications perform a variety of functions and provide amazing features and utilities to their users; but deep down, it’s really all just creating, reading, updating and deleting data.                          
####Installations                                                                   
1)python3                                                                                                                 
2)vagrant                                                                                     
3)virtualbox                                                                                            
4)Flask                                                                                   
5)Sqlalchemy                                                                                      
6)Oauth                                                                                                       
Process:                                                                                  
--sudo apt-get install vagrant                          
--sudo apt-get install virtualbox                                                                                   '
--vagrant init ubuntu/xenial64                                                                                    
--vagrant ssh                                                                             
--cd /vagrant                                                                                                         
--source flask-env/bin/activate                                                                                                       
####Running:
1)create database:                                  
python database_setup.py                                                                                              
2)Push data to database                                         
python products.py                                                                      
3)final output :                                              
python project.py                                                   

# ezEMS Planner

This application was developed as a Hackbright Academy four-week project. It uses publicly available data from [DataSF](https://data.sfgov.org/Public-Safety/Fire-Department-Calls-for-Service/nuek-vuh3) to predict the ambulance arrival time at a given address and to calculate statistics about the ambulance system in SF.

The prediction is based on a random forest regression model fitted to data recorded between 2000 and 2019. Of a total of approximately 5.1 million records in the database, 3.3 million are listed as medical incidents and they required a total of 1.7 million ambulance units being dispatched—1.4 million from the fire department and 300,000 million private units. The app uses this filtered dataset of 1.7 million entries recorded between 2000–2019.

All the data was stored in a PostgreSQL database, whose tables are depicted in the diagram below:

![alt text](https://github.com/gogrean/SFFD-Medical-Incident-Calls/blob/master/code/flaskr/static/figs/db_schema.png "Database Tables")

The following features were extracted from the information in the database and later used to fit the random forest regression model:

**Temporal Features**

* `Year`
* `Day of Year_sin`
* `Day of Year_cos`
* `Day of Week_sin`
* `Day of Week_cos`
* `Hour_sin`
* `Hour_cos`
* `is_Weekend` (boolean)
* `is_Holiday` (boolean)

**Spatial Features**

* `Latitude`
* `Longitude`
* `Tract` (GEOID10 from 2010 US Census)
* `Nearest Hospital` (distance)
* `Nearest Fire Station` (distance)

**Dispatcher Input**

* `Original Priority` (3, 2, or E)
* `Unit Type` (private or fire department)

Some of the temporal features above were decomposed into sine and cosine components, to account for their circularity (e.g., 23:00 is closer to midnight than to 21:00, but Python would have no way of knowing this if the time was simply converted to a number, because 23 is closer to 21 than it is to 0.)

The data was split into 75% training data and 25% testing data, and a grid search was conducted over a set of 176 combinations of random forest regression model parameters (11 `n_estimators` values between 50 and 300, 8 `min_samples_split` values between 2 and 400, and 2 `max_features` values of "log2" and "auto"). The best-fitting model had `n_estimators = 175`, `min_samples_split = 200`, and `max_features = "log2"`.

![alt text](https://github.com/gogrean/SFFD-Medical-Incident-Calls/blob/master/code/flaskr/static/figs/feature_importance_rfr.png "Feature Importance Values for the RFR Model")

The graph above shows the importance of the features in the best-fitting model. Input features related to the same human-interpretable parameter were combined (e.g., `Hour_cos` and `Hour_sin`).

The uncertainty on the predicted ambulance arrival time is approximately 3.5 minutes, which is an improvement of 24% over a naive guess. Additional features, such as live travel time to the incident, ambulance post locations, commuter-adjusted population estimates, and homelessness data would likely improve the accuracy of the prediction.

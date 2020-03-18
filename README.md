# ezEMS Planner
Hackbright Academy Project

This application was developed as a Hackbright Academy four-week project. It uses publicly available data from [DataSF](https://data.sfgov.org/Public-Safety/Fire-Department-Calls-for-Service/nuek-vuh3) to predict the ambulance arrival time at a given address and to calculate statistics about the ambulance system in SF.

The prediction is based on a random forest regression model fitted to data recorded between 2000 and 2019. Of a total of approximately 5.1 million records in the database, 3.3 million are listed as medical incidents and they required a total of 1.7 million ambulance units being dispatched—1.4 million from the fire department and 300,000 million private units. The app uses this filtered dataset of 1.7 million entries recorded between 2000–2019.

All the data was stored in a PostgreSQL database, whose tables are depicted in the diagram below:

![alt text]( "Schema")

CREATE TABLE person( -- https://schema.org/Person
    personid VARCHAR(255), 
    givenname VARCHAR(255), -- https://schema.org/givenName
    familyname VARCHAR(255), -- https://schema.org/familyName
    identifier VARCHAR (255), -- https://schema.org/identifier
    PRIMARY KEY(personid)


);

CREATE TABLE experiment(
    experimentid VARCHAR(255), 
    date DATETIME,
    name VARCHAR(255),
    creatorid VARCHAR(255), https://schema.org/creator
    PRIMARY_KEY(experimentid),
    FOREIGN KEY(creatorid) REFERENCES person(personid)
);

INSERT INTO PERSON (person_id, givenname, familyname, identifier) VALUES ('PERSON1', 'Meier', 'Andreas', 'https://orcid.org/0009-0002-6541-4637');
INSERT INTO PERSON (person_id, givenname, familyname, identifier) VALUES ('PERSON2', 'Fuentes', 'Juan', 'https://orcid.org/0009-0002-8209-1999');


INSERT INTO experiment (experimentid, date, name, creatorid) VALUES ('EXPERIMENT1', '2025-09-08 08:41:50', 'Example Experiment', 'Person1');



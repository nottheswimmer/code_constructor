# Code Constructor

Takes a JSON payload and converts it to code that defines classes or structures in many languages.

## TODO

- Identify bugs and write tests
- Add more languages
- Output usage examples as well (currently only implemented for Python)
- String methods (currently only implemented for Python)
- Optional getters and setters for Java
- Marshalling / Unmarshalling support in Go
- Reserved keyword and builtin shadowing protection (currently only implemented for Python)

## Supported Languages

- Python
- Go
- C
- Java

## Caveats

- No support for null values.
- No support for arrays of different types (TODO: Perhaps implement enums)
- For arrays and strings in languages that require a fixed array size as part of the struct (e.g. C),
  the length given in the payload is used for strings, or the maximum length for arrays.

## Examples

### Squad (example taken from the Mozilla Docs)

```python
    squad = MetaClass.from_json("Squad", """\
{
  "squadName": "Super hero squad",
  "homeTown": "Metro City",
  "formed": 2016,
  "secretBase": "Super tower",
  "active": true,
  "members": [
    {
      "name": "Molecule Man",
      "age": 29,
      "secretIdentity": "Dan Jukes",
      "powers": [
        "Radiation resistance",
        "Turning tiny",
        "Radiation blast"
      ]
    },
    {
      "name": "Madame Uppercut",
      "age": 39,
      "secretIdentity": "Jane Wilson",
      "powers": [
        "Million tonne punch",
        "Damage resistance",
        "Superhuman reflexes"
      ]
    },
    {
      "name": "Eternal Flame",
      "age": 1000000,
      "secretIdentity": "Unknown",
      "powers": [
        "Immortality",
        "Heat Immunity",
        "Inferno",
        "Teleportation",
        "Interdimensional travel"
      ]
    }
  ]
}
""")
    squad._dump()
```

[To Python]
```python
class Member:
    def __init__(self, name: str, age: int, secret_identity: str, powers: List[str]):
        self.name = name
        self.age = age
        self.secret_identity = secret_identity
        self.powers = powers

    def __repr__(self):
        return f"Member(name={self.name!r}, age={self.age!r}, secret_identity={self.secret_identity!r}, powers={self.powers!r})"

class Squad:
    def __init__(self, squad_name: str, home_town: str, formed: int, secret_base: str, active: bool, members: List['Member']):
        self.squad_name = squad_name
        self.home_town = home_town
        self.formed = formed
        self.secret_base = secret_base
        self.active = active
        self.members = members

    def __repr__(self):
        return f"Squad(squad_name={self.squad_name!r}, home_town={self.home_town!r}, formed={self.formed!r}, secret_base={self.secret_base!r}, active={self.active!r}, members={self.members!r})"

squad = Squad(squad_name='Super hero squad', home_town='Metro City', formed=2016, secret_base='Super tower', active=True, members=[Member(name='Molecule Man', age=29, secret_identity='Dan Jukes', powers=['Radiation resistance', 'Turning tiny', 'Radiation blast']), Member(name='Madame Uppercut', age=39, secret_identity='Jane Wilson', powers=['Million tonne punch', 'Damage resistance', 'Superhuman reflexes']), Member(name='Eternal Flame', age=1000000, secret_identity='Unknown', powers=['Immortality', 'Heat Immunity', 'Inferno', 'Teleportation', 'Interdimensional travel'])])
print(squad)
```

[To Java]
```java
class Squad {
    public String squadName;
    public String homeTown;
    public int formed;
    public String secretBase;
    public boolean active;
    public Member[] members;

    public Squad(String squadName, String homeTown, int formed, String secretBase, boolean active, Member[] members) {
        this.squadName = squadName;
        this.homeTown = homeTown;
        this.formed = formed;
        this.secretBase = secretBase;
        this.active = active;
        this.members = members;
    }
}

class Member {
    public String name;
    public int age;
    public String secretIdentity;
    public String[] powers;

    public Member(String name, int age, String secretIdentity, String[] powers) {
        this.name = name;
        this.age = age;
        this.secretIdentity = secretIdentity;
        this.powers = powers;
    }
}
```

[To Go]
```go
type Member struct {
    Name string
    Age int
    SecretIdentity string
    Powers []string
}

type Squad struct {
    SquadName string
    HomeTown string
    Formed int
    SecretBase string
    Active bool
    Members []Member
}
```

[To C]
```c
#include <stdbool.h>

struct Member {
    char name[12];
    int age;
    char secret_identity[9];
    char powers[20][3];
};

struct Squad {
    char squad_name[16];
    char home_town[10];
    int formed;
    char secret_base[11];
    bool active;
    Member members[3];
};
```

### Course from the Blackboard API

Input:

```python
    course = MetaClass.from_json("course", """\
{
  "id": "string",
  "uuid": "string",
  "externalId": "string",
  "dataSourceId": "string",
  "courseId": "string",
  "name": "string",
  "description": "string",
  "created": "2020-08-30T23:47:15.769Z",
  "modified": "2020-08-30T23:47:15.769Z",
  "organization": true,
  "ultraStatus": "Undecided",
  "allowGuests": true,
  "closedComplete": true,
  "termId": "string",
  "availability": {
    "available": "Yes",
    "duration": {
      "type": "Continuous",
      "start": "2020-08-30T23:47:15.769Z",
      "end": "2020-08-30T23:47:15.769Z",
      "daysOfUse": 0
    }
  },
  "enrollment": {
    "type": "InstructorLed",
    "start": "2020-08-30T23:47:15.769Z",
    "end": "2020-08-30T23:47:15.769Z",
    "accessCode": "string"
  },
  "locale": {
    "id": "string",
    "force": true
  },
  "hasChildren": true,
  "parentId": "string",
  "externalAccessUrl": "string",
  "guestAccessUrl": "string"
}
""")
    course._dump()
```

Output:

[To Python]
```python
class Duration:
    def __init__(self, type_field: str, start: str, end: str, days_of_use: int):
        self.type_field = type_field
        self.start = start
        self.end = end
        self.days_of_use = days_of_use

    def __repr__(self):
        return f"Duration(type_field={self.type_field!r}, start={self.start!r}, end={self.end!r}, days_of_use={self.days_of_use!r})"

class Availability:
    def __init__(self, available: str, duration: 'Duration'):
        self.available = available
        self.duration = duration

    def __repr__(self):
        return f"Availability(available={self.available!r}, duration={self.duration!r})"

class Enrollment:
    def __init__(self, type_field: str, start: str, end: str, access_code: str):
        self.type_field = type_field
        self.start = start
        self.end = end
        self.access_code = access_code

    def __repr__(self):
        return f"Enrollment(type_field={self.type_field!r}, start={self.start!r}, end={self.end!r}, access_code={self.access_code!r})"

class Locale:
    def __init__(self, id_field: str, force: bool):
        self.id_field = id_field
        self.force = force

    def __repr__(self):
        return f"Locale(id_field={self.id_field!r}, force={self.force!r})"

class Course:
    def __init__(self, id_field: str, uuid: str, external_id: str, data_source_id: str, course_id: str, name: str, description: str, created: str, modified: str, organization: bool, ultra_status: str, allow_guests: bool, closed_complete: bool, term_id: str, availability: 'Availability', enrollment: 'Enrollment', locale: 'Locale', has_children: bool, parent_id: str, external_access_url: str, guest_access_url: str):
        self.id_field = id_field
        self.uuid = uuid
        self.external_id = external_id
        self.data_source_id = data_source_id
        self.course_id = course_id
        self.name = name
        self.description = description
        self.created = created
        self.modified = modified
        self.organization = organization
        self.ultra_status = ultra_status
        self.allow_guests = allow_guests
        self.closed_complete = closed_complete
        self.term_id = term_id
        self.availability = availability
        self.enrollment = enrollment
        self.locale = locale
        self.has_children = has_children
        self.parent_id = parent_id
        self.external_access_url = external_access_url
        self.guest_access_url = guest_access_url

    def __repr__(self):
        return f"Course(id_field={self.id_field!r}, uuid={self.uuid!r}, external_id={self.external_id!r}, data_source_id={self.data_source_id!r}, course_id={self.course_id!r}, name={self.name!r}, description={self.description!r}, created={self.created!r}, modified={self.modified!r}, organization={self.organization!r}, ultra_status={self.ultra_status!r}, allow_guests={self.allow_guests!r}, closed_complete={self.closed_complete!r}, term_id={self.term_id!r}, availability={self.availability!r}, enrollment={self.enrollment!r}, locale={self.locale!r}, has_children={self.has_children!r}, parent_id={self.parent_id!r}, external_access_url={self.external_access_url!r}, guest_access_url={self.guest_access_url!r})"

course = Course(id_field='string', uuid='string', external_id='string', data_source_id='string', course_id='string', name='string', description='string', created='2020-08-30T23:47:15.769Z', modified='2020-08-30T23:47:15.769Z', organization=True, ultra_status='Undecided', allow_guests=True, closed_complete=True, term_id='string', availability=Availability(available='Yes', duration=Duration(type_field='Continuous', start='2020-08-30T23:47:15.769Z', end='2020-08-30T23:47:15.769Z', days_of_use=0)), enrollment=Enrollment(type_field='InstructorLed', start='2020-08-30T23:47:15.769Z', end='2020-08-30T23:47:15.769Z', access_code='string'), locale=Locale(id_field='string', force=True), has_children=True, parent_id='string', external_access_url='string', guest_access_url='string')
print(course)
```

[To Java]
```java
class Course {
    public String id;
    public String uuid;
    public String externalId;
    public String dataSourceId;
    public String courseId;
    public String name;
    public String description;
    public String created;
    public String modified;
    public boolean organization;
    public String ultraStatus;
    public boolean allowGuests;
    public boolean closedComplete;
    public String termId;
    public Availability availability;
    public Enrollment enrollment;
    public Locale locale;
    public boolean hasChildren;
    public String parentId;
    public String externalAccessUrl;
    public String guestAccessUrl;

    public Course(String id, String uuid, String externalId, String dataSourceId, String courseId, String name, String description, String created, String modified, boolean organization, String ultraStatus, boolean allowGuests, boolean closedComplete, String termId, Availability availability, Enrollment enrollment, Locale locale, boolean hasChildren, String parentId, String externalAccessUrl, String guestAccessUrl) {
        this.id = id;
        this.uuid = uuid;
        this.externalId = externalId;
        this.dataSourceId = dataSourceId;
        this.courseId = courseId;
        this.name = name;
        this.description = description;
        this.created = created;
        this.modified = modified;
        this.organization = organization;
        this.ultraStatus = ultraStatus;
        this.allowGuests = allowGuests;
        this.closedComplete = closedComplete;
        this.termId = termId;
        this.availability = availability;
        this.enrollment = enrollment;
        this.locale = locale;
        this.hasChildren = hasChildren;
        this.parentId = parentId;
        this.externalAccessUrl = externalAccessUrl;
        this.guestAccessUrl = guestAccessUrl;
    }
}

class Availability {
    public String available;
    public Duration duration;

    public Availability(String available, Duration duration) {
        this.available = available;
        this.duration = duration;
    }
}

class Duration {
    public String type;
    public String start;
    public String end;
    public int daysOfUse;

    public Duration(String type, String start, String end, int daysOfUse) {
        this.type = type;
        this.start = start;
        this.end = end;
        this.daysOfUse = daysOfUse;
    }
}

class Enrollment {
    public String type;
    public String start;
    public String end;
    public String accessCode;

    public Enrollment(String type, String start, String end, String accessCode) {
        this.type = type;
        this.start = start;
        this.end = end;
        this.accessCode = accessCode;
    }
}

class Locale {
    public String id;
    public boolean force;

    public Locale(String id, boolean force) {
        this.id = id;
        this.force = force;
    }
}
```

[To Go]
```go
type Duration struct {
    Type string
    Start string
    End string
    DaysOfUse int
}

type Availability struct {
    Available string
    Duration Duration
}

type Enrollment struct {
    Type string
    Start string
    End string
    AccessCode string
}

type Locale struct {
    Id string
    Force bool
}

type Course struct {
    Id string
    Uuid string
    ExternalId string
    DataSourceId string
    CourseId string
    Name string
    Description string
    Created string
    Modified string
    Organization bool
    UltraStatus string
    AllowGuests bool
    ClosedComplete bool
    TermId string
    Availability Availability
    Enrollment Enrollment
    Locale Locale
    HasChildren bool
    ParentId string
    ExternalAccessUrl string
    GuestAccessUrl string
}
```

[To C]
```c
#include <stdbool.h>

struct Duration {
    char type[10];
    char start[24];
    char end[24];
    int days_of_use;
};

struct Availability {
    char available[3];
    Duration duration;
};

struct Enrollment {
    char type[13];
    char start[24];
    char end[24];
    char access_code[6];
};

struct Locale {
    char id[6];
    bool force;
};

struct Course {
    char id[6];
    char uuid[6];
    char external_id[6];
    char data_source_id[6];
    char course_id[6];
    char name[6];
    char description[6];
    char created[24];
    char modified[24];
    bool organization;
    char ultra_status[9];
    bool allow_guests;
    bool closed_complete;
    char term_id[6];
    Availability availability;
    Enrollment enrollment;
    Locale locale;
    bool has_children;
    char parent_id[6];
    char external_access_url[6];
    char guest_access_url[6];
};
```
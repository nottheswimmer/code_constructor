# Code Constructor

Takes a JSON payload and converts it to code that defines classes or structures in many languages.

## TODO

- Identify bugs and write tests
- Add more languages
- Output usage examples as well
- Optional getters and setters for Java
- Marshalling / Unmarshalling support in Go
- Reserved keyword and builtin shadowing protection (currently only implemented in Python)

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

## Example

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
    def __init__(self, type: str, start: str, end: str, days_of_use: int):
        self.type = type
        self.start = start
        self.end = end
        self.days_of_use = days_of_use

class Availability:
    def __init__(self, available: str, duration: 'Duration'):
        self.available = available
        self.duration = duration

class Enrollment:
    def __init__(self, type: str, start: str, end: str, access_code: str):
        self.type = type
        self.start = start
        self.end = end
        self.access_code = access_code

class Locale:
    def __init__(self, id: str, force: bool):
        self.id = id
        self.force = force

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
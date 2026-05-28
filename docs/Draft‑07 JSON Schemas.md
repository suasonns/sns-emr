**0) Shared Definitions (use this file as common.defs.schema.json)**



{

&#x20; "$schema": "http://json-schema.org/draft-07/schema#",

&#x20; "$id": "https://sns-hospice-emr/schemas/common.defs.schema.json",

&#x20; "title": "SNS Hospice EMR Common Definitions (Draft-07)",

&#x20; "type": "object",

&#x20; "definitions": {

&#x20;   "uuid": {

&#x20;     "type": "string",

&#x20;     "pattern": "^\[0-9a-fA-F]{8}-\[0-9a-fA-F]{4}-\[1-5]\[0-9a-fA-F]{3}-\[89abAB]\[0-9a-fA-F]{3}-\[0-9a-fA-F]{12}$"

&#x20;   },

&#x20;   "dateTime": {

&#x20;     "type": "string",

&#x20;     "format": "date-time"

&#x20;   },

&#x20;   "nullableDateTime": {

&#x20;     "type": \["string", "null"],

&#x20;     "format": "date-time"

&#x20;   },

&#x20;   "nullableUuid": {

&#x20;     "type": \["string", "null"],

&#x20;     "pattern": "^\[0-9a-fA-F]{8}-\[0-9a-fA-F]{4}-\[1-5]\[0-9a-fA-F]{3}-\[89abAB]\[0-9a-fA-F]{3}-\[0-9a-fA-F]{12}$"

&#x20;   },

&#x20;   "discipline": {

&#x20;     "type": "string",

&#x20;     "enum": \["RN", "MSW", "SC", "MD", "NP", "LVN", "CHHA"]

&#x20;   },

&#x20;   "status": {

&#x20;     "type": "string",

&#x20;     "enum": \["DRAFT", "SIGNED", "VOIDED"]

&#x20;   },

&#x20;   "evidenceLink": {

&#x20;     "type": "object",

&#x20;     "additionalProperties": false,

&#x20;     "required": \["reference\_type", "reference\_id"],

&#x20;     "properties": {

&#x20;       "reference\_type": {

&#x20;         "type": "string",

&#x20;         "enum": \["VISIT", "DOCUMENT", "NOTE", "ASSESSMENT"]

&#x20;       },

&#x20;       "reference\_id": { "$ref": "#/definitions/nullableUuid" }

&#x20;     }

&#x20;   },

&#x20;   "painAssessment": {

&#x20;     "type": "object",

&#x20;     "additionalProperties": false,

&#x20;     "required": \["assessed", "patient\_alert", "tool\_used", "pain\_present"],

&#x20;     "properties": {

&#x20;       "assessed": { "type": "boolean" },

&#x20;       "patient\_alert": { "type": "boolean" },

&#x20;       "tool\_used": { "type": "string", "enum": \["NUMERIC", "FLACC", "PAINAD"] },

&#x20;       "pain\_present": { "type": "boolean" },

&#x20;       "severity": { "type": \["number", "integer", "null"], "minimum": 0, "maximum": 10 },

&#x20;       "location": { "type": \["string", "null"], "maxLength": 200 },

&#x20;       "intervention\_or\_escalation": { "type": \["string", "null"], "maxLength": 2000 }

&#x20;     },

&#x20;     "allOf": \[

&#x20;       {

&#x20;         "if": { "properties": { "patient\_alert": { "const": true } }, "required": \["patient\_alert"] },

&#x20;         "then": { "properties": { "tool\_used": { "const": "NUMERIC" } } },

&#x20;         "else": { "properties": { "tool\_used": { "enum": \["FLACC", "PAINAD"] } } }

&#x20;       }

&#x20;     ]

&#x20;   },

&#x20;   "discrepancy": {

&#x20;     "type": "object",

&#x20;     "additionalProperties": false,

&#x20;     "required": \["alignment\_to\_rn\_baseline", "requires\_idg\_reconciliation"],

&#x20;     "properties": {

&#x20;       "alignment\_to\_rn\_baseline": {

&#x20;         "type": "string",

&#x20;         "enum": \["NOT\_APPLICABLE", "ALIGNED", "DIFFERENT"]

&#x20;       },

&#x20;       "discrepancy\_note": { "type": \["string", "null"], "maxLength": 4000 },

&#x20;       "requires\_idg\_reconciliation": { "type": "boolean" }

&#x20;     },

&#x20;     "allOf": \[

&#x20;       {

&#x20;         "if": { "properties": { "alignment\_to\_rn\_baseline": { "const": "DIFFERENT" } } },

&#x20;         "then": {

&#x20;           "required": \["discrepancy\_note"],

&#x20;           "properties": { "requires\_idg\_reconciliation": { "const": true } }

&#x20;         }

&#x20;       }

&#x20;     ]

&#x20;   }

&#x20; }

}



**1) Base Assessment Schema (use as assessment.base.schema.json)**



{

&#x20; "$schema": "http://json-schema.org/draft-07/schema#",

&#x20; "$id": "https://sns-hospice-emr/schemas/assessment.base.schema.json",

&#x20; "title": "SNS Assessment Base (Draft-07)",

&#x20; "type": "object",

&#x20; "additionalProperties": false,

&#x20; "required": \[

&#x20;   "schema\_version",

&#x20;   "patient\_id",

&#x20;   "discipline",

&#x20;   "assessment\_type",

&#x20;   "occurred\_at",

&#x20;   "status",

&#x20;   "evidence\_link",

&#x20;   "pain\_assessment",

&#x20;   "discrepancy",

&#x20;   "meta"

&#x20; ],

&#x20; "properties": {

&#x20;   "schema\_version": { "type": "string", "pattern": "^1\\\\.3$" },

&#x20;   "patient\_id": { "$ref": "common.defs.schema.json#/definitions/uuid" },

&#x20;   "discipline": { "$ref": "common.defs.schema.json#/definitions/discipline" },

&#x20;   "assessment\_type": {

&#x20;     "type": "string",

&#x20;     "enum": \[

&#x20;       "RN\_ICA",

&#x20;       "MSW\_ICA",

&#x20;       "SC\_ICA",

&#x20;       "RN\_BEREAVEMENT\_BASELINE",

&#x20;       "BEREAVEMENT\_ASSESSMENT",

&#x20;       "DISCIPLINE\_VISIT\_NOTE"

&#x20;     ]

&#x20;   },

&#x20;   "occurred\_at": { "$ref": "common.defs.schema.json#/definitions/dateTime" },

&#x20;   "status": { "$ref": "common.defs.schema.json#/definitions/status" },

&#x20;   "signed\_at": { "$ref": "common.defs.schema.json#/definitions/nullableDateTime" },

&#x20;   "signed\_by": { "$ref": "common.defs.schema.json#/definitions/nullableUuid" },

&#x20;   "evidence\_link": { "$ref": "common.defs.schema.json#/definitions/evidenceLink" },

&#x20;   "pain\_assessment": { "$ref": "common.defs.schema.json#/definitions/painAssessment" },

&#x20;   "discrepancy": { "$ref": "common.defs.schema.json#/definitions/discrepancy" },

&#x20;   "meta": {

&#x20;     "type": "object",

&#x20;     "additionalProperties": false,

&#x20;     "required": \["created\_via", "tenant\_id"],

&#x20;     "properties": {

&#x20;       "created\_via": { "type": "string", "enum": \["UI", "API", "IMPORT"] },

&#x20;       "source\_form": { "type": \["string", "null"], "maxLength": 200 },

&#x20;       "tenant\_id": { "$ref": "common.defs.schema.json#/definitions/uuid" }

&#x20;     }

&#x20;   }

&#x20; },

&#x20; "allOf": \[

&#x20;   {

&#x20;     "if": { "properties": { "status": { "const": "SIGNED" } }, "required": \["status"] },

&#x20;     "then": {

&#x20;       "required": \["signed\_at", "signed\_by"],

&#x20;       "properties": {

&#x20;         "signed\_at": { "type": "string", "format": "date-time" },

&#x20;         "signed\_by": { "$ref": "common.defs.schema.json#/definitions/uuid" },

&#x20;         "evidence\_link": {

&#x20;           "properties": {

&#x20;             "reference\_id": { "$ref": "common.defs.schema.json#/definitions/uuid" }

&#x20;           }

&#x20;         }

&#x20;       }

&#x20;     }

&#x20;   }

&#x20; ]

}



**2) RN ICA Schema (assessment.rn\_ica.schema.json)**



{

&#x20; "$schema": "http://json-schema.org/draft-07/schema#",

&#x20; "$id": "https://sns-hospice-emr/schemas/assessment.rn\_ica.schema.json",

&#x20; "title": "RN Initial Comprehensive Assessment (RN\_ICA) — Draft-07",

&#x20; "allOf": \[

&#x20;   { "$ref": "assessment.base.schema.json" },

&#x20;   {

&#x20;     "type": "object",

&#x20;     "additionalProperties": false,

&#x20;     "required": \["soc", "ros", "safety\_fall", "rn\_bereavement\_baseline"],

&#x20;     "properties": {

&#x20;       "discipline": { "const": "RN" },

&#x20;       "assessment\_type": { "const": "RN\_ICA" },



&#x20;       "soc": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["soc\_at", "soc\_source"],

&#x20;         "properties": {

&#x20;           "soc\_at": { "$ref": "common.defs.schema.json#/definitions/dateTime" },

&#x20;           "soc\_source": { "type": "string", "enum": \["RN\_INITIAL\_ASSESSMENT", "ELECTION\_ORDER"] }

&#x20;         }

&#x20;       },



&#x20;       "ros": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["integumentary"],

&#x20;         "properties": {

&#x20;           "integumentary": {

&#x20;             "type": "object",

&#x20;             "additionalProperties": false,

&#x20;             "required": \["skin\_assessed", "wound\_present", "education"],

&#x20;             "properties": {

&#x20;               "skin\_assessed": { "type": "boolean", "const": true },

&#x20;               "skin\_intact": { "type": \["boolean", "null"] },

&#x20;               "skin\_impaired": { "type": \["boolean", "null"] },

&#x20;               "risk\_factors": {

&#x20;                 "type": "array",

&#x20;                 "items": {

&#x20;                   "type": "string",

&#x20;                   "enum": \[

&#x20;                     "poor\_nutrition",

&#x20;                     "incontinence",

&#x20;                     "immobility\_weakness",

&#x20;                     "advanced\_age",

&#x20;                     "altered\_sensation",

&#x20;                     "edema",

&#x20;                     "other"

&#x20;                   ]

&#x20;                 },

&#x20;                 "uniqueItems": true

&#x20;               },

&#x20;               "wound\_present": { "type": "boolean" },

&#x20;               "skin\_impairment\_assessment\_ref": {

&#x20;                 "type": "object",

&#x20;                 "additionalProperties": false,

&#x20;                 "required": \["reference\_type", "reference\_id"],

&#x20;                 "properties": {

&#x20;                   "reference\_type": { "type": "string", "enum": \["DOCUMENT", "NOTE", "ASSESSMENT"] },

&#x20;                   "reference\_id": { "$ref": "common.defs.schema.json#/definitions/nullableUuid" }

&#x20;                 }

&#x20;               },

&#x20;               "education": {

&#x20;                 "type": "object",

&#x20;                 "additionalProperties": false,

&#x20;                 "required": \["provided", "pcg\_understanding"],

&#x20;                 "properties": {

&#x20;                   "provided": { "type": "boolean" },

&#x20;                   "topics": {

&#x20;                     "type": "array",

&#x20;                     "items": {

&#x20;                       "type": "string",

&#x20;                       "enum": \["repositioning\_q2h", "pressure\_offloading", "skin\_monitoring", "report\_changes"]

&#x20;                     },

&#x20;                     "uniqueItems": true

&#x20;                   },

&#x20;                   "pcg\_understanding": { "type": "boolean" }

&#x20;                 }

&#x20;               },

&#x20;               "narrative": { "type": \["string", "null"], "maxLength": 8000 }

&#x20;             },

&#x20;             "allOf": \[

&#x20;               {

&#x20;                 "if": { "properties": { "wound\_present": { "const": true } }, "required": \["wound\_present"] },

&#x20;                 "then": {

&#x20;                   "properties": {

&#x20;                     "skin\_impairment\_assessment\_ref": {

&#x20;                       "properties": { "reference\_id": { "$ref": "common.defs.schema.json#/definitions/uuid" } }

&#x20;                     }

&#x20;                   }

&#x20;                 }

&#x20;               }

&#x20;             ]

&#x20;           }

&#x20;         }

&#x20;       },



&#x20;       "safety\_fall": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \[

&#x20;           "care\_setting",

&#x20;           "fall\_risk\_assessed",

&#x20;           "fall\_risk\_level",

&#x20;           "history\_of\_falls\_reviewed",

&#x20;           "mobility\_limitations\_documented",

&#x20;           "assistive\_devices\_reviewed",

&#x20;           "facility\_path",

&#x20;           "home\_path"

&#x20;         ],

&#x20;         "properties": {

&#x20;           "care\_setting": { "type": "string", "enum": \["FACILITY", "HOME"] },

&#x20;           "fall\_risk\_assessed": { "type": "boolean", "const": true },

&#x20;           "fall\_risk\_level": { "type": "string", "enum": \["LOW", "MODERATE", "HIGH"] },

&#x20;           "history\_of\_falls\_reviewed": { "type": "boolean" },

&#x20;           "mobility\_limitations\_documented": { "type": "boolean" },

&#x20;           "assistive\_devices\_reviewed": { "type": "boolean" },



&#x20;           "facility\_path": {

&#x20;             "type": "object",

&#x20;             "additionalProperties": false,

&#x20;             "required": \["facility\_protocols\_reviewed", "call\_light\_confirmed", "alarms\_reviewed", "facility\_responsible", "facility\_staff\_notified"],

&#x20;             "properties": {

&#x20;               "facility\_protocols\_reviewed": { "type": "boolean" },

&#x20;               "call\_light\_confirmed": { "type": "boolean" },

&#x20;               "alarms\_reviewed": { "type": "boolean" },

&#x20;               "facility\_responsible": { "type": "boolean" },

&#x20;               "facility\_staff\_notified": { "type": "boolean" }

&#x20;             }

&#x20;           },



&#x20;           "home\_path": {

&#x20;             "type": "object",

&#x20;             "additionalProperties": false,

&#x20;             "required": \["hazards\_assessed", "bathroom\_safety\_reviewed", "bed\_chair\_safety\_reviewed", "oxygen\_safety\_reviewed", "emergency\_preparedness\_reviewed", "education\_within\_scope", "pcg\_understanding"],

&#x20;             "properties": {

&#x20;               "hazards\_assessed": { "type": "boolean" },

&#x20;               "bathroom\_safety\_reviewed": { "type": "boolean" },

&#x20;               "bed\_chair\_safety\_reviewed": { "type": "boolean" },

&#x20;               "oxygen\_safety\_reviewed": { "type": "boolean" },

&#x20;               "emergency\_preparedness\_reviewed": { "type": "boolean" },

&#x20;               "education\_within\_scope": { "type": "boolean" },

&#x20;               "pcg\_understanding": { "type": "boolean" }

&#x20;             }

&#x20;           }

&#x20;         },

&#x20;         "allOf": \[

&#x20;           {

&#x20;             "if": { "properties": { "care\_setting": { "const": "FACILITY" } }, "required": \["care\_setting"] },

&#x20;             "then": {

&#x20;               "properties": {

&#x20;                 "facility\_path": {

&#x20;                   "properties": {

&#x20;                     "facility\_responsible": { "const": true }

&#x20;                   }

&#x20;                 }

&#x20;               }

&#x20;             }

&#x20;           },

&#x20;           {

&#x20;             "if": { "properties": { "care\_setting": { "const": "HOME" } }, "required": \["care\_setting"] },

&#x20;             "then": {

&#x20;               "properties": {

&#x20;                 "home\_path": {

&#x20;                   "properties": {

&#x20;                     "education\_within\_scope": { "const": true }

&#x20;                   }

&#x20;                 }

&#x20;               }

&#x20;             }

&#x20;           }

&#x20;         ]

&#x20;       },



&#x20;       "rn\_bereavement\_baseline": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["documented", "summary"],

&#x20;         "properties": {

&#x20;           "documented": { "type": "boolean", "const": true },

&#x20;           "primary\_caregiver\_identified": { "type": "boolean" },

&#x20;           "primary\_bereaved\_identified": { "type": "boolean" },

&#x20;           "early\_indicators": {

&#x20;             "type": "array",

&#x20;             "items": {

&#x20;               "type": "string",

&#x20;               "enum": \["anticipatory\_grief", "caregiver\_strain", "limited\_support", "emotional\_distress", "none\_noted"]

&#x20;             },

&#x20;             "uniqueItems": true

&#x20;           },

&#x20;           "summary": { "type": "string", "maxLength": 4000 },

&#x20;           "risk\_hint": { "type": "string", "enum": \["NONE", "LOW", "MODERATE", "HIGH"] }

&#x20;         }

&#x20;       }

&#x20;     }

&#x20;   }

&#x20; ]

}



**3) MSW ICA Schema (assessment.msw\_ica.schema.json)**



{

&#x20; "$schema": "http://json-schema.org/draft-07/schema#",

&#x20; "$id": "https://sns-hospice-emr/schemas/assessment.msw\_ica.schema.json",

&#x20; "title": "MSW ICA (MSW\_ICA) — Draft-07",

&#x20; "allOf": \[

&#x20;   { "$ref": "assessment.base.schema.json" },

&#x20;   {

&#x20;     "type": "object",

&#x20;     "additionalProperties": false,

&#x20;     "required": \["rn\_baseline\_panel", "rn\_baseline\_ack", "psychosocial"],

&#x20;     "properties": {

&#x20;       "discipline": { "const": "MSW" },

&#x20;       "assessment\_type": { "const": "MSW\_ICA" },



&#x20;       "rn\_baseline\_panel": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["rn\_ica\_ref", "rn\_bereavement\_baseline\_ref"],

&#x20;         "properties": {

&#x20;           "rn\_ica\_ref": { "$ref": "common.defs.schema.json#/definitions/evidenceLink" },

&#x20;           "rn\_bereavement\_baseline\_ref": { "$ref": "common.defs.schema.json#/definitions/evidenceLink" },

&#x20;           "rn\_skin\_baseline\_ref": { "$ref": "common.defs.schema.json#/definitions/evidenceLink" },

&#x20;           "rn\_safety\_fall\_baseline\_ref": { "$ref": "common.defs.schema.json#/definitions/evidenceLink" }

&#x20;         }

&#x20;       },



&#x20;       "rn\_baseline\_ack": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["reviewed", "reviewed\_at"],

&#x20;         "properties": {

&#x20;           "reviewed": { "type": "boolean", "const": true },

&#x20;           "reviewed\_at": { "$ref": "common.defs.schema.json#/definitions/dateTime" }

&#x20;         }

&#x20;       },



&#x20;       "psychosocial": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["support\_system", "risk\_screen", "narrative"],

&#x20;         "properties": {

&#x20;           "mental\_status": { "type": \["string", "null"], "maxLength": 500 },

&#x20;           "coping": { "type": \["string", "null"], "maxLength": 500 },

&#x20;           "caregiver\_capacity": { "type": \["string", "null"], "maxLength": 500 },

&#x20;           "support\_system": {

&#x20;             "type": "array",

&#x20;             "items": { "type": "string", "maxLength": 80 },

&#x20;             "minItems": 0,

&#x20;             "uniqueItems": true

&#x20;           },

&#x20;           "financial\_legal\_needs": {

&#x20;             "type": "object",

&#x20;             "additionalProperties": false,

&#x20;             "properties": {

&#x20;               "financial\_concerns": { "type": "boolean" },

&#x20;               "advance\_directives\_reviewed": { "type": "boolean" },

&#x20;               "poa\_identified": { "type": "boolean" },

&#x20;               "burial\_planning": { "type": "string", "enum": \["IN\_PROCESS", "COMPLETE", "NEEDS\_HELP", "NOT\_APPLICABLE"] }

&#x20;             }

&#x20;           },

&#x20;           "risk\_screen": {

&#x20;             "type": "object",

&#x20;             "additionalProperties": false,

&#x20;             "required": \["crisis\_risk", "abuse\_neglect\_risk", "suicide\_risk"],

&#x20;             "properties": {

&#x20;               "crisis\_risk": { "type": "string", "enum": \["NONE", "LOW", "MODERATE", "HIGH"] },

&#x20;               "abuse\_neglect\_risk": { "type": "boolean" },

&#x20;               "suicide\_risk": { "type": "boolean" }

&#x20;             }

&#x20;           },

&#x20;           "narrative": { "type": "string", "maxLength": 10000 }

&#x20;         }

&#x20;       }

&#x20;     }

&#x20;   }

&#x20; ]

}



**4) SC ICA Schema (assessment.sc\_ica.schema.json)**



{

&#x20; "$schema": "http://json-schema.org/draft-07/schema#",

&#x20; "$id": "https://sns-hospice-emr/schemas/assessment.sc\_ica.schema.json",

&#x20; "title": "SC ICA (SC\_ICA) — Draft-07",

&#x20; "allOf": \[

&#x20;   { "$ref": "assessment.base.schema.json" },

&#x20;   {

&#x20;     "type": "object",

&#x20;     "additionalProperties": false,

&#x20;     "required": \["rn\_baseline\_panel", "rn\_baseline\_ack", "spiritual"],

&#x20;     "properties": {

&#x20;       "discipline": { "const": "SC" },

&#x20;       "assessment\_type": { "const": "SC\_ICA" },



&#x20;       "rn\_baseline\_panel": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["rn\_ica\_ref", "rn\_bereavement\_baseline\_ref"],

&#x20;         "properties": {

&#x20;           "rn\_ica\_ref": { "$ref": "common.defs.schema.json#/definitions/evidenceLink" },

&#x20;           "rn\_bereavement\_baseline\_ref": { "$ref": "common.defs.schema.json#/definitions/evidenceLink" }

&#x20;         }

&#x20;       },



&#x20;       "rn\_baseline\_ack": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["reviewed", "reviewed\_at"],

&#x20;         "properties": {

&#x20;           "reviewed": { "type": "boolean", "const": true },

&#x20;           "reviewed\_at": { "$ref": "common.defs.schema.json#/definitions/dateTime" }

&#x20;         }

&#x20;       },



&#x20;       "spiritual": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["support\_sources", "spiritual\_distress", "interventions", "narrative", "declined\_spiritual\_care"],

&#x20;         "properties": {

&#x20;           "faith\_background": { "type": \["string", "null"], "maxLength": 500 },

&#x20;           "cultural\_influences": { "type": \["string", "null"], "maxLength": 500 },

&#x20;           "support\_sources": {

&#x20;             "type": "array",

&#x20;             "items": { "type": "string", "maxLength": 80 },

&#x20;             "uniqueItems": true

&#x20;           },

&#x20;           "spiritual\_distress": {

&#x20;             "type": "object",

&#x20;             "additionalProperties": false,

&#x20;             "required": \["present", "indicators"],

&#x20;             "properties": {

&#x20;               "present": { "type": "boolean" },

&#x20;               "indicators": {

&#x20;                 "type": "array",

&#x20;                 "items": { "type": "string", "maxLength": 80 },

&#x20;                 "uniqueItems": true

&#x20;               }

&#x20;             }

&#x20;           },

&#x20;           "interventions": {

&#x20;             "type": "array",

&#x20;             "items": { "type": "string", "maxLength": 80 },

&#x20;             "uniqueItems": true

&#x20;           },

&#x20;           "narrative": { "type": "string", "maxLength": 10000 },

&#x20;           "declined\_spiritual\_care": { "type": "boolean" }

&#x20;         }

&#x20;       }

&#x20;     }

&#x20;   }

&#x20; ]

}



**5) RN Bereavement Baseline Schema (assessment.rn\_bereavement\_baseline.schema.json)**



{

&#x20; "$schema": "http://json-schema.org/draft-07/schema#",

&#x20; "$id": "https://sns-hospice-emr/schemas/assessment.rn\_bereavement\_baseline.schema.json",

&#x20; "title": "RN Bereavement Baseline (RN\_BEREAVEMENT\_BASELINE) — Draft-07",

&#x20; "allOf": \[

&#x20;   { "$ref": "assessment.base.schema.json" },

&#x20;   {

&#x20;     "type": "object",

&#x20;     "additionalProperties": false,

&#x20;     "required": \["baseline"],

&#x20;     "properties": {

&#x20;       "discipline": { "const": "RN" },

&#x20;       "assessment\_type": { "const": "RN\_BEREAVEMENT\_BASELINE" },

&#x20;       "baseline": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["primary\_bereaved\_identified", "primary\_caregiver\_identified", "early\_indicators", "rn\_summary"],

&#x20;         "properties": {

&#x20;           "primary\_bereaved\_identified": { "type": "boolean" },

&#x20;           "relationship": { "type": \["string", "null"], "maxLength": 120 },

&#x20;           "primary\_caregiver\_identified": { "type": "boolean" },

&#x20;           "support\_system": {

&#x20;             "type": "array",

&#x20;             "items": { "type": "string", "maxLength": 80 },

&#x20;             "uniqueItems": true

&#x20;           },

&#x20;           "early\_indicators": {

&#x20;             "type": "array",

&#x20;             "items": {

&#x20;               "type": "string",

&#x20;               "enum": \["anticipatory\_grief", "caregiver\_strain", "limited\_support", "emotional\_distress", "none\_noted"]

&#x20;             },

&#x20;             "uniqueItems": true

&#x20;           },

&#x20;           "rn\_summary": { "type": "string", "maxLength": 4000 }

&#x20;         }

&#x20;       }

&#x20;     }

&#x20;   }

&#x20; ]

}



**6) Bereavement Assessment Schema (assessment.bereavement\_assessment.schema.json)**



{

&#x20; "$schema": "http://json-schema.org/draft-07/schema#",

&#x20; "$id": "https://sns-hospice-emr/schemas/assessment.bereavement\_assessment.schema.json",

&#x20; "title": "Bereavement Assessment (BEREAVEMENT\_ASSESSMENT) — Draft-07",

&#x20; "allOf": \[

&#x20;   { "$ref": "assessment.base.schema.json" },

&#x20;   {

&#x20;     "type": "object",

&#x20;     "additionalProperties": false,

&#x20;     "required": \["rn\_baseline\_panel", "rn\_baseline\_ack", "primary\_bereaved", "risk\_assessment", "plan", "narrative"],

&#x20;     "properties": {

&#x20;       "assessment\_type": { "const": "BEREAVEMENT\_ASSESSMENT" },



&#x20;       "rn\_baseline\_panel": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["rn\_bereavement\_baseline\_ref"],

&#x20;         "properties": {

&#x20;           "rn\_bereavement\_baseline\_ref": { "$ref": "common.defs.schema.json#/definitions/evidenceLink" }

&#x20;         }

&#x20;       },



&#x20;       "rn\_baseline\_ack": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["reviewed", "reviewed\_at", "alignment"],

&#x20;         "properties": {

&#x20;           "reviewed": { "type": "boolean", "const": true },

&#x20;           "reviewed\_at": { "$ref": "common.defs.schema.json#/definitions/dateTime" },

&#x20;           "alignment": { "type": "string", "enum": \["ALIGNED", "DIFFERENT"] },

&#x20;           "difference\_note": { "type": \["string", "null"], "maxLength": 4000 }

&#x20;         },

&#x20;         "allOf": \[

&#x20;           {

&#x20;             "if": { "properties": { "alignment": { "const": "DIFFERENT" } } },

&#x20;             "then": { "required": \["difference\_note"] }

&#x20;           }

&#x20;         ]

&#x20;       },



&#x20;       "primary\_bereaved": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["last\_name", "first\_name", "relationship\_to\_patient", "was\_primary\_caregiver", "preferred\_contact\_method", "consent\_to\_contact\_post\_death"],

&#x20;         "properties": {

&#x20;           "last\_name": { "type": "string", "maxLength": 100 },

&#x20;           "first\_name": { "type": "string", "maxLength": 100 },

&#x20;           "age": { "type": \["integer", "null"], "minimum": 0, "maximum": 120 },

&#x20;           "address": { "type": \["string", "null"], "maxLength": 250 },

&#x20;           "phone\_home": { "type": \["string", "null"], "maxLength": 50 },

&#x20;           "phone\_cell": { "type": \["string", "null"], "maxLength": 50 },

&#x20;           "relationship\_to\_patient": { "type": "string", "maxLength": 120 },

&#x20;           "was\_primary\_caregiver": { "type": "boolean" },

&#x20;           "preferred\_contact\_method": { "type": "string", "enum": \["PHONE", "TEXT", "EMAIL", "MAIL"] },

&#x20;           "consent\_to\_contact\_post\_death": { "type": "boolean" }

&#x20;         }

&#x20;       },



&#x20;       "risk\_assessment": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["risk\_items", "total\_score", "risk\_level"],

&#x20;         "properties": {

&#x20;           "risk\_items": {

&#x20;             "type": "array",

&#x20;             "minItems": 1,

&#x20;             "items": {

&#x20;               "type": "object",

&#x20;               "additionalProperties": false,

&#x20;               "required": \["code", "selected", "weight"],

&#x20;               "properties": {

&#x20;                 "code": { "type": "string", "maxLength": 80 },

&#x20;                 "selected": { "type": "boolean" },

&#x20;                 "weight": { "type": "integer", "minimum": 0, "maximum": 50 }

&#x20;               }

&#x20;             }

&#x20;           },

&#x20;           "total\_score": { "type": "integer", "minimum": 0, "maximum": 500 },

&#x20;           "risk\_level": { "type": "string", "enum": \["LOW", "MODERATE", "HIGH"] }

&#x20;         }

&#x20;       },



&#x20;       "additional\_bereaved": {

&#x20;         "type": "array",

&#x20;         "items": {

&#x20;           "type": "object",

&#x20;           "additionalProperties": false,

&#x20;           "required": \["name", "relationship"],

&#x20;           "properties": {

&#x20;             "name": { "type": "string", "maxLength": 160 },

&#x20;             "relationship": { "type": "string", "maxLength": 120 },

&#x20;             "phone": { "type": \["string", "null"], "maxLength": 50 },

&#x20;             "specific\_concerns": { "type": \["string", "null"], "maxLength": 500 }

&#x20;           }

&#x20;         }

&#x20;       },



&#x20;       "plan": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["services\_offered", "family\_response"],

&#x20;         "properties": {

&#x20;           "services\_offered": {

&#x20;             "type": "array",

&#x20;             "items": {

&#x20;               "type": "string",

&#x20;               "enum": \["EDUCATION", "PHONE\_FOLLOWUP", "COUNSELING\_VISIT", "SPIRITUAL\_SUPPORT", "SUPPORT\_GROUP\_REFERRAL", "COMMUNITY\_REFERRAL"]

&#x20;             },

&#x20;             "uniqueItems": true

&#x20;           },

&#x20;           "family\_response": { "type": "string", "enum": \["ACCEPTED", "DECLINED", "DEFERRED"] },

&#x20;           "decline\_reason": { "type": \["string", "null"], "maxLength": 1000 },

&#x20;           "reoffer\_date": { "type": \["string", "null"], "format": "date-time" }

&#x20;         },

&#x20;         "allOf": \[

&#x20;           {

&#x20;             "if": { "properties": { "family\_response": { "const": "DECLINED" } } },

&#x20;             "then": { "required": \["decline\_reason"] }

&#x20;           }

&#x20;         ]

&#x20;       },



&#x20;       "narrative": { "type": "string", "maxLength": 10000 }

&#x20;     }

&#x20;   }

&#x20; ]

}



**7) Generic Discipline Visit Note Schema (assessment.discipline\_visit\_note.schema.json)**



{

&#x20; "$schema": "http://json-schema.org/draft-07/schema#",

&#x20; "$id": "https://sns-hospice-emr/schemas/assessment.discipline\_visit\_note.schema.json",

&#x20; "title": "Generic Discipline Visit Note (DISCIPLINE\_VISIT\_NOTE) — Draft-07",

&#x20; "allOf": \[

&#x20;   { "$ref": "assessment.base.schema.json" },

&#x20;   {

&#x20;     "type": "object",

&#x20;     "additionalProperties": false,

&#x20;     "required": \["note"],

&#x20;     "properties": {

&#x20;       "assessment\_type": { "const": "DISCIPLINE\_VISIT\_NOTE" },

&#x20;       "discipline": { "enum": \["MD", "NP", "LVN", "CHHA"] },

&#x20;       "note": {

&#x20;         "type": "object",

&#x20;         "additionalProperties": false,

&#x20;         "required": \["summary"],

&#x20;         "properties": {

&#x20;           "summary": { "type": "string", "maxLength": 8000 },

&#x20;           "interventions": {

&#x20;             "type": "array",

&#x20;             "items": { "type": "string", "maxLength": 300 },

&#x20;             "uniqueItems": true

&#x20;           },

&#x20;           "education": {

&#x20;             "type": "array",

&#x20;             "items": { "type": "string", "maxLength": 300 },

&#x20;             "uniqueItems": true

&#x20;           }

&#x20;         }

&#x20;       }

&#x20;     }

&#x20;   }

&#x20; ]

}



**8) Optional: One “Master Schema” using oneOf (use as assessment.master.schema.json)**



{

&#x20; "$schema": "http://json-schema.org/draft-07/schema#",

&#x20; "$id": "https://sns-hospice-emr/schemas/assessment.master.schema.json",

&#x20; "title": "SNS Assessment Master (oneOf) — Draft-07",

&#x20; "oneOf": \[

&#x20;   { "$ref": "assessment.rn\_ica.schema.json" },

&#x20;   { "$ref": "assessment.msw\_ica.schema.json" },

&#x20;   { "$ref": "assessment.sc\_ica.schema.json" },

&#x20;   { "$ref": "assessment.rn\_bereavement\_baseline.schema.json" },

&#x20;   { "$ref": "assessment.bereavement\_assessment.schema.json" },

&#x20;   { "$ref": "assessment.discipline\_visit\_note.schema.json" }

&#x20; ]

}


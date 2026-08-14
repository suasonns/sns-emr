export type InboxThread = {
  id: string;
  sender: string;
  senderRole: string;
  subject: string;
  preview: string;
  time: string;
  unread: boolean;
  tag: string;
};

export type InboxResponse = {
  unread_count: number;
  threads: InboxThread[];
};

const DEMO_THREADS: InboxThread[] = [
  {
    id: "demo-1",
    sender: "Dr. Sarah Jenkins",
    senderRole: "Attending Physician",
    subject: "Verify George Henderson Oxygen Flow",
    preview: "O2 flow rate stabilized above 92% during the clinic call. Please monitor SpO2 at your visit and document.",
    time: "08:15 AM",
    unread: true,
    tag: "Inbox",
  },
  {
    id: "demo-2",
    sender: "John Sterling",
    senderRole: "Clinical Director",
    subject: "Albert Smith HIS Review Approved",
    preview: "Great job completing the clinical signature list for Albert. Everything looks compliant and ready for batch export.",
    time: "08:45 AM",
    unread: true,
    tag: "Inbox",
  },
  {
    id: "demo-3",
    sender: "Pharmacy Team",
    senderRole: "Partner Pharmacy",
    subject: "Medication Delivery Confirmation - Harold Finch",
    preview: "Morphine sulfate and sublingual drops have been delivered to the patient's residence via courier.",
    time: "Yesterday",
    unread: false,
    tag: "Sent",
  },
  {
    id: "demo-4",
    sender: "Maria Santos, RN",
    senderRole: "Self",
    subject: "Draft: Wound Progress Report - Eleanor Vance",
    preview: "Eleanor's sacral pressure ulcer is showing signs of healing with granulating tissue. No active infection present.",
    time: "Yesterday",
    unread: false,
    tag: "Drafts",
  },
  {
    id: "demo-5",
    sender: "Lab Results - Auto",
    senderRole: "Integration Engine",
    subject: "ALERT: Lab Results Available for George Henderson",
    preview: "Hospice lab intake: Chem-7 results are back. Elevated BUN/Creatinine detected. Click to sync to patient's chart.",
    time: "2 days ago",
    unread: false,
    tag: "Archived",
  },
  {
    id: "demo-6",
    sender: "Care Team",
    senderRole: "Inbox",
    subject: "New secure message from agency",
    preview: "A new message thread is ready in the secure inbox workspace.",
    time: "3 days ago",
    unread: false,
    tag: "Inbox",
  },
];

export function getDemoInbox(): InboxResponse {
  return {
    unread_count: DEMO_THREADS.filter((thread) => thread.unread).length,
    threads: DEMO_THREADS,
  };
}

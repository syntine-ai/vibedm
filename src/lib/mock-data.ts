export const user = {
  firstName: "Alex",
  lastName: "Morgan",
  email: "alex@example.com",
  phone: "+1 555 0100",
  plan: "free" as "free" | "pro",
  igConnected: false,
  igUsername: "alex.creates",
  dmUsage: 142,
  dmLimit: 1000,
  contactUsage: 89,
  contactLimit: 1000,
};

export type Automation = {
  id: string;
  name: string;
  status: "active" | "inactive";
  createdAt: string;
  modifiedAt: string;
  triggerType: string;
};

export const automations: Automation[] = [
  {
    id: "a1",
    name: "Reel Giveaway — Summer Drop",
    status: "active",
    createdAt: "3 days ago",
    modifiedAt: "2 hours ago",
    triggerType: "Comment on Post/Reel",
  },
  {
    id: "a2",
    name: "DM Welcome Flow",
    status: "active",
    createdAt: "1 week ago",
    modifiedAt: "Yesterday",
    triggerType: "DM",
  },
  {
    id: "a3",
    name: "Story Reply → Discount",
    status: "inactive",
    createdAt: "2 weeks ago",
    modifiedAt: "5 days ago",
    triggerType: "Story Reply",
  },
];

export const contacts = [
  { id: "c1", username: "sarah.lee", name: "Sarah Lee", phone: "+1 555 0142", email: "sarah@x.com", source: "Reel Giveaway", date: "2h ago" },
  { id: "c2", username: "mikepaints", name: "Mike Adams", phone: "", email: "mike@x.com", source: "DM Welcome", date: "1d ago" },
  { id: "c3", username: "the.jen", name: "Jen Park", phone: "+1 555 0190", email: "", source: "Story Reply", date: "3d ago" },
];

export const products = [
  { id: "p1", name: "Linen Tee — Sand", price: 38, link: "https://shop.x/tee" },
  { id: "p2", name: "Sunset Print A2", price: 24, link: "https://shop.x/print" },
  { id: "p3", name: "Workshop Pass", price: 120, link: "https://shop.x/pass" },
];

export const orders = [
  { id: "o1", contact: "@sarah.lee", product: "Linen Tee — Sand", amount: 38, status: "completed" as const, date: "Today" },
  { id: "o2", contact: "@mikepaints", product: "Sunset Print A2", amount: 24, status: "pending" as const, date: "Yesterday" },
  { id: "o3", contact: "@the.jen", product: "Workshop Pass", amount: 120, status: "completed" as const, date: "3d ago" },
];

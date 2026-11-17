export type Role = "seller" | "organizer";

export interface StaffMember {
  readonly name: string;
  readonly role: Role;
}

import type { Transporter } from "nodemailer";
import type { Customer } from "../../domain/models.ts";
import type { Notifier } from "../../services/notifications.ts";

export class NodemailerNotifier implements Notifier {
  private readonly transport: Transporter;
  private readonly sender: string;

  constructor(transport: Transporter, sender: string) {
    this.transport = transport;
    this.sender = sender;
  }

  async send(customer: Customer, message: string): Promise<void> {
    const subject = message.split("\n")[0];
    const info = await this.transport.sendMail({
      from: this.sender,
      to: { name: customer.name, address: customer.email },
      subject,
      text: message,
    });
    console.log(`[email via nodemailer -> ${customer.email}] "${subject}" id ${info.messageId}\n`);
  }
}

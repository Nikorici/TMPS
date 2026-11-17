export class PaymentDeclined extends Error {
  override name = "PaymentDeclined";
}

export class SoldOut extends Error {
  override name = "SoldOut";
}

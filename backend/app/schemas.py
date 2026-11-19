from __future__ import annotations

from datetime import date, time
from typing import Any, Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class TwoFactorVerifyRequest(BaseModel):
    twofa_token: str
    code: str = Field(min_length=6, max_length=32)


class TwoFactorEnableRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class TwoFactorDisableRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=3, max_length=200)
    document_number: str = Field(min_length=3, max_length=50)
    phone: str | None = None
    email: str
    password: str = Field(min_length=8, max_length=128)
    pdn_consent: bool = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class RefreshRequest(BaseModel):
    refresh_token: str


class SettingsUpdate(BaseModel):
    theme: Literal["light", "dark", "system"] = "system"
    language: Literal["ru", "en"] = "ru"
    date_format: str = "dd.MM.yyyy"
    number_format: str = "space_comma"
    page_size: Literal[10, 25, 50] = 25
    saved_filters: list[dict[str, Any]] = Field(default_factory=list)


class PublicBookingCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=200)
    document_number: str = Field(min_length=3, max_length=50)
    phone: str | None = None
    email: str | None = None
    pdn_consent: bool = True
    room_id: int
    rate_id: int
    checkin_date: date
    checkout_date: date
    promo_code: str | None = None
    adults: int = Field(default=1, ge=1, le=10)
    children: int = Field(default=0, ge=0, le=10)
    payment_method: Literal["CARD", "ONLINE", "CASH", "BANK_TRANSFER"] = "ONLINE"
    payment_amount: float = 0
    source: Literal["SITE", "PHONE", "WALK_IN", "OTA"] = "SITE"
    arrival_time: time | None = None
    hold_minutes: int = Field(default=60, ge=5, le=1440)
    points_to_use: int = Field(default=0, ge=0)
    special_requests: str | None = Field(default=None, max_length=1000)


class ManagerBookingCreate(BaseModel):
    guest_id: int
    room_id: int
    rate_id: int
    checkin_date: date
    checkout_date: date
    promo_id: int | None = None
    adults: int = Field(default=1, ge=1, le=10)
    children: int = Field(default=0, ge=0, le=10)
    source: Literal["SITE", "PHONE", "WALK_IN", "OTA"] = "SITE"
    arrival_time: time | None = None
    hold_minutes: int = Field(default=60, ge=5, le=1440)


class MoveBookingRequest(BaseModel):
    room_id: int
    checkin_date: date
    checkout_date: date


class CheckInRequest(BaseModel):
    document_number: str
    deposit_amount: float = 0
    payment_method: Literal["CARD", "CASH", "BANK_TRANSFER", "ONLINE"] = "CARD"


class CheckOutRequest(BaseModel):
    payment_amount: float = 0
    payment_method: Literal["CARD", "CASH", "BANK_TRANSFER", "ONLINE"] = "CARD"


class PaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    method: Literal["CARD", "CASH", "BANK_TRANSFER", "ONLINE"] = "CARD"
    payment_type: Literal["PAYMENT", "DEPOSIT"] = "PAYMENT"


class RefundCreate(BaseModel):
    amount: float = Field(gt=0)
    reason: str = Field(min_length=3, max_length=255)


class ServiceOrderCreate(BaseModel):
    service_id: int
    quantity: int = Field(default=1, ge=1, le=100)


class NightAuditRequest(BaseModel):
    business_date: date


class RoomStatusUpdate(BaseModel):
    status_name: str
    reason_id: int | None = None


class HousekeepingTaskCreate(BaseModel):
    room_id: int
    staff_id: int | None = None
    task_type: Literal["DAILY", "POST_CHECKOUT", "ON_REQUEST"] = "DAILY"
    priority: Literal["LOW", "NORMAL", "HIGH", "URGENT"] = "NORMAL"


class ConsumableWriteOff(BaseModel):
    consumable_id: int
    quantity: float = Field(gt=0)


class MaintenanceCreate(BaseModel):
    room_id: int
    description: str = Field(min_length=3, max_length=2000)
    priority: Literal["LOW", "NORMAL", "HIGH", "URGENT"] = "NORMAL"
    task_id: int | None = None
    assigned_to: int | None = None


class MaintenanceStatusUpdate(BaseModel):
    status: Literal["OPEN", "IN_PROGRESS", "DONE", "CANCELLED"]


class UserCreate(BaseModel):
    role_id: int
    full_name: str = Field(min_length=3, max_length=200)
    email: str
    phone: str | None = None
    password: str = Field(min_length=8, max_length=128)
    is_active: bool = True


class UserUpdate(BaseModel):
    role_id: int | None = None
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class RoleAssignRequest(BaseModel):
    role_id: int


class RolePermissionsUpdate(BaseModel):
    permission_codes: list[str]


class GuestCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=200)
    document_number: str = Field(min_length=3, max_length=50)
    phone: str | None = None
    email: str | None = None
    pdn_consent: bool = True


class ImportCommitRequest(BaseModel):
    filename: str | None = None
    rows: list[dict[str, Any]]


class HoldUpdateRequest(BaseModel):
    arrival_time: time | None = None
    hold_minutes: int = Field(default=60, ge=5, le=1440)


class BlockUserRequest(BaseModel):
    reason_id: int | None = None
    custom_reason: str | None = Field(default=None, max_length=500)


class ChangeBookingRequest(BaseModel):
    checkin_date: date
    checkout_date: date


class SpecialRequestsUpdate(BaseModel):
    special_requests: str | None = Field(default=None, max_length=1000)


class ReviewCreate(BaseModel):
    booking_id: int
    rating: int = Field(ge=1, le=5)
    title: str | None = Field(default=None, max_length=150)
    body: str = Field(min_length=10, max_length=2000)


class ReviewModerateRequest(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
    comment: str | None = Field(default=None, max_length=500)


class WaitlistCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=200)
    email: str | None = None
    phone: str | None = None
    room_type_id: int | None = None
    checkin_date: date
    checkout_date: date
    adults: int = Field(default=1, ge=1, le=10)
    children: int = Field(default=0, ge=0, le=10)
    note: str | None = Field(default=None, max_length=1000)


class WaitlistUpdate(BaseModel):
    status: Literal["WAITING", "NOTIFIED", "CONVERTED", "CANCELLED"]
    note: str | None = Field(default=None, max_length=1000)


class BulkBookingAction(BaseModel):
    ids: list[int]
    action: Literal["confirm", "cancel"]


class TemplateSendRequest(BaseModel):
    guest_id: int
    template_id: int | None = None
    subject: str | None = Field(default=None, max_length=200)
    body: str | None = Field(default=None, max_length=2000)

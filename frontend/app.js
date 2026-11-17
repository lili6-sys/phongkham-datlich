
"use strict";

// API se duoc ket noi qua cung dia chi website
const API_BASE = "/api";

let currentUser = null;
let accessToken = null;

// Goi API
async function apiRequest(path, options = {}) {
    const headers = {
        ...options.headers
    };

    if (options.body) {
        headers["Content-Type"] = "application/json";
    }

    if (accessToken) {
        headers["Authorization"] = `Bearer ${accessToken}`;
    }

    const response = await fetch(API_BASE + path, {
        ...options,
        headers
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
        let message = "Yeu cau khong thanh cong";

        if (typeof data?.detail === "string") {
            message = data.detail;
        } else if (response.status === 404) {
            message = "API chua san sang";
        } else {
            message += ` (HTTP ${response.status})`;
        }

        throw new Error(message);
    }

    return data;
}

// Tao the thong tin an toan
function createCard(title, lines) {
    const card = document.createElement("div");
    card.className = "card";

    const heading = document.createElement("h3");
    heading.textContent = title;
    card.appendChild(heading);

    lines.forEach(line => {
        const p = document.createElement("p");
        p.textContent = line;
        card.appendChild(p);
    });

    return card;
}

// Chuyen trang
function showPage(pageId) {
    document.querySelectorAll(".page").forEach(page => {
        page.hidden = page.id !== pageId;
    });

    document.querySelectorAll(".navbar button").forEach(btn => {
        btn.classList.toggle(
            "active",
            btn.dataset.page === pageId
        );
    });

    if (pageId === "booking") {
        loadDoctorOptions();
        if (currentUser && currentUser.role === "patient") {
            document.getElementById("patientUsername").value =
                currentUser.username;
        }
    }
}

// Gan su kien cho menu
document.querySelectorAll(".navbar button").forEach(button => {
    button.addEventListener("click", () => {
        showPage(button.dataset.page);
    });
});

showPage("home");

// Hien thi danh sach bac si
async function loadDoctors() {
    const list = document.getElementById("doctorList");
    list.textContent = "Dang tai danh sach bac si...";

    try {
        const doctors = await apiRequest("/doctors/");

        list.replaceChildren();

        if (doctors.length === 0) {
            list.textContent = "Chua co bac si nao.";
            return;
        }

        doctors.forEach(doctor => {
            const card = createCard(
                doctor.full_name,
                [
                    `Ma bac si: ${doctor.id}`,
                    `Ma chuyen khoa: ${doctor.specialty_id}`,
                    `So dien thoai: ${doctor.phone || "Chua cap nhat"}`,
                    `Trang thai: ${doctor.is_active ? "Dang hoat dong" : "Ngung hoat dong"}`
                ]
            );

            list.appendChild(card);
        });

    } catch (error) {
        list.textContent = "Khong tai duoc bac si: " + error.message;
    }
}

document.getElementById("loadDoctors")
    .addEventListener("click", loadDoctors);

// Dua bac si vao o chon khi dat lich
async function loadDoctorOptions() {
    const select = document.getElementById("doctorId");

    select.replaceChildren(
        new Option("-- Chon bac si --", "")
    );

    try {
        const doctors = await apiRequest("/doctors/");

        doctors
            .filter(doctor => doctor.is_active)
            .forEach(doctor => {
                select.add(
                    new Option(doctor.full_name, doctor.id)
                );
            });

    } catch (error) {
        document.getElementById("bookingMessage").textContent =
            "Khong tai duoc danh sach bac si: " + error.message;
    }
}

// Dat lich kham
document.getElementById("bookingForm")
    .addEventListener("submit", async event => {
        event.preventDefault();

        const message = document.getElementById("bookingMessage");

        const username = document.getElementById(
            "patientUsername"
        ).value.trim();

        const doctorId = Number(
            document.getElementById("doctorId").value
        );

        const localTime = document.getElementById(
            "appointmentTime"
        ).value;

        const note = document.getElementById("note").value.trim();

        if (!currentUser) {
            message.textContent = "Hay dang nhap truoc khi dat lich.";
            return;
        }

        if (!username || !doctorId || !localTime) {
            message.textContent = "Vui long nhap day du thong tin.";
            return;
        }

        const date = new Date(localTime);

        if (Number.isNaN(date.getTime())) {
            message.textContent = "Ngay gio khong hop le.";
            return;
        }

        if (date <= new Date()) {
            message.textContent = "Hay chon thoi gian trong tuong lai.";
            return;
        }

        message.textContent = "Dang gui yeu cau dat lich...";

        try {
            const result = await apiRequest("/appointments/", {
                method: "POST",
                body: JSON.stringify({
                    patient_username: username,
                    doctor_id: doctorId,
                    appointment_time: date.toISOString(),
                    note: note || null
                })
            });

            message.textContent =
                `Dat lich thanh cong! Ma lich hen: ${result.id}`;

            event.target.reset();

        } catch (error) {
            message.textContent = "Dat lich that bai: " + error.message;
        }
    });

// Hien thi lich hen cho admin
async function loadAppointments() {
    const list = document.getElementById("appointmentList");

    if (!currentUser || currentUser.role !== "admin") {
        list.textContent =
            "Can dang nhap bang tai khoan quan tri de xem lich hen.";
        return;
    }

    list.textContent = "Dang tai danh sach lich hen...";

    try {
        const appointments = await apiRequest("/appointments/");

        list.replaceChildren();

        if (appointments.length === 0) {
            list.textContent = "Chua co lich hen nao.";
            return;
        }

        appointments.forEach(item => {
            const card = createCard(
                `Lich hen #${item.id}`,
                [
                    `Benh nhan: ${item.patient_username}`,
                    `Ma bac si: ${item.doctor_id}`,
                    `Thoi gian: ${new Date(item.appointment_time).toLocaleString("vi-VN")}`,
                    `Trang thai: ${item.status}`
                ]
            );

            list.appendChild(card);
        });

    } catch (error) {
        list.textContent = "Khong tai duoc lich hen: " + error.message;
    }
}

document.getElementById("loadAppointments")
    .addEventListener("click", loadAppointments);

// Dang nhap bang API cua Linh
document.getElementById("loginForm")
    .addEventListener("submit", async event => {
        event.preventDefault();

        const message = document.getElementById("loginMessage");

        const username = document.getElementById(
            "username"
        ).value.trim();

        const password = document.getElementById(
            "password"
        ).value;

        message.textContent = "Dang dang nhap...";

        try {
            const result = await apiRequest("/auth/login", {
                method: "POST",
                body: JSON.stringify({
                    username,
                    password
                })
            });

            if (!result.access_token) {
                throw new Error("API khong tra ve token");
            }

            accessToken = result.access_token;

            currentUser = {
                username: result.username,
                role: result.role
            };

            message.textContent =
                `Dang nhap thanh cong: ${result.username} (${result.role})`;

            document.getElementById("password").value = "";

        } catch (error) {
            accessToken = null;
            currentUser = null;

            message.textContent =
                "Dang nhap that bai: " + error.message;
        }
    });

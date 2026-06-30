# Betaa24_RidderPanel
Beta24 Rider Management System is a Django and MySQL-based platform for managing rider onboarding, training, document verification, task tracking, and automated payouts. It supports Excel data import, real-time analytics, payment tracking, and performance monitoring, helping logistics teams streamline rider operations efficiently.
# Beta24 Rider Management System

A comprehensive Rider Operations and Payout Management Platform built with Django and MySQL to streamline rider onboarding, training tracking, task management, payment settlements, and business analytics.

## 🚀 Overview

Beta24 Rider Management System is designed to manage the complete lifecycle of delivery riders, from app download and onboarding to training completion, document verification, task tracking, and weekly payouts. The platform provides a centralized dashboard for operations teams to monitor rider performance, customer payments, pending settlements, and business metrics in real time.

## ✨ Key Features

### 📥 Bulk Rider Import

* Upload rider data directly from Excel (.xlsx/.csv) files.
* Automatic data extraction and storage in MySQL.
* Duplicate detection and centralized rider database.

### 🚴 Rider Onboarding & Tracking

* Rider registration and profile management.
* Training status tracking.
* Manual reason capture for incomplete training.
* Document verification workflow.
* Active and inactive rider management.

### 📄 Document Management

* Track document submission status.
* Verification and approval process.
* Real-time onboarding progress monitoring.

### 📦 Task Management

* Manual task entry and tracking.
* Record task date, duration, distance, and completion details.
* Track task cancellation reasons (Rider or Customer initiated).
* Complete task history and reporting.

### 💰 Automated Payout Calculation

Business rules automatically calculate rider earnings based on:

* Base Plan: ₹24.5 for 1 task, up to 10 minutes and 2 KM.
* Additional Task: ₹25 per extra task.
* Additional Time: ₹1 per extra minute.
* Additional Distance: ₹10 per extra kilometer.

### 💳 Settlement & Payment Management

* Weekly rider payout calculations.
* Paid vs Pending amount tracking.
* Customer pending payment monitoring.
* Company settlement reports.

### 📊 Advanced Dashboard & Analytics

* Total Riders
* Active Riders
* Training Pending Riders
* Documents Pending Riders
* Weekly Revenue
* Rider Performance Leaderboard
* Payout Summary
* Customer Payment Analytics
* Revenue and Task Performance Charts

### 🔔 Smart Notifications

* Pending training alerts
* Document verification reminders
* Pending payout notifications
* Customer payment reminders

## 🛠 Technology Stack

* Backend: Python, Django, Django REST Framework
* Database: MySQL
* Frontend: Bootstrap 5, HTML5, CSS3, JavaScript
* Data Processing: Pandas, OpenPyXL
* Charts & Analytics: Chart.js / ApexCharts
* Authentication: Django Authentication System

## 📈 Business Benefits

* Centralized rider management.
* Faster onboarding process.
* Accurate payout calculations.
* Reduced manual settlement errors.
* Real-time operational insights.
* Improved rider performance tracking.

## 🎯 Use Cases

* Hyperlocal delivery startups
* Last-mile logistics companies
* Gig workforce management platforms
* Delivery operations teams
* Rider onboarding and payout management systems

Beta24 Rider Management System is a scalable and production-ready platform that simplifies rider operations, improves operational efficiency, and provides complete visibility into onboarding, tasks, and financial settlements.

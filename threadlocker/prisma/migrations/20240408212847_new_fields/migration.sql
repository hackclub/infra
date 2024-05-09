-- CreateTable
CREATE TABLE "Thread" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "admin" TEXT NOT NULL,
    "lock_type" TEXT NOT NULL,
    "time" DATETIME,
    "reason" TEXT NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "Thread_id_key" ON "Thread"("id");

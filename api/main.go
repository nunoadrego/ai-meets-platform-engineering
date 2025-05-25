package main

import (
	"database/sql"
	"net/http"

	"github.com/gin-gonic/gin"

	_ "github.com/lib/pq"
)

var db *sql.DB

func main() {
	var err error
	db, err = sql.Open("postgres", "user=postgres password=password dbname=apps sslmode=disable")
	if err != nil {
		panic(err)
	}
	defer db.Close()

	router := gin.Default()
	router.GET("/apps", getApps)
	router.GET("/apps/:id", getAppDetails)
	router.Run(":8080")
}

func getApps(c *gin.Context) {
	rows, err := db.Query("SELECT id, name FROM apps")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to query apps"})
		return
	}
	defer rows.Close()

	var apps []App
	for rows.Next() {
		var app App
		if err := rows.Scan(&app.ID, &app.Name); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to scan app"})
			return
		}
		apps = append(apps, app)
	}
	c.JSON(http.StatusOK, apps)
}

func getAppDetails(c *gin.Context) {
	var app AppDetails
	err := db.QueryRow("SELECT id, name, owner, language, framework FROM apps WHERE id = $1", c.Param("id")).
		Scan(&app.ID, &app.Name, &app.Owner, &app.Language, &app.Framework)
	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"error": "App not found"})
		return
	} else if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to query app"})
		return
	}
	c.JSON(http.StatusOK, app)
}

type App struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

type AppDetails struct {
	ID        int    `json:"id"`
	Name      string `json:"name"`
	Owner     string `json:"owner"`
	Language  string `json:"language"`
	Framework string `json:"framework"`
}

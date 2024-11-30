"use client";

import React, { useCallback, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthContext } from "@/context/AuthContext";
import LogoutButton from "../components/LogoutButton";
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Grid2,
  Card,
  CardActionArea,
  CardContent,
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  DialogActions,
} from "@mui/material";

type GroupData = {
  group_id: string;
  group_name: string;
  creator_id: string;
  time_created: Date;
  time_updated: Date;
};

type UserData = {
  user_id: string;
  username: string;
  email: string;
};

type UserIdMapping = {
  [key: string]: UserData;
};

export default function DashboardPage() {
  const authContext = useContext(AuthContext);
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  // For displaying user groups
  const [groups, setGroups] = useState([]);
  const [userIdMapping, setUserIdMapping] = useState({} as UserIdMapping);
  // For creating new groups
  const [openDialog, setOpenDialog] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");
  const [creatingGroup, setCreatingGroup] = useState(false);
  const [createError, setCreateError] = useState("");

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authContext?.isAuthenticated) {
      console.log("User is not authenticated");
      router.push("/login");
    }
  }, [authContext?.isAuthenticated, router]);

  const fetchGroups = useCallback(() => {
    setLoading(true);
    setError("");
    const accessToken = localStorage.getItem("access_token");

    if (accessToken) {
      fetch("/api/user/groups", {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })
        .then((response) => {
          if (response.ok) return response.json();
          else if (response.status === 401 || response.status === 403) {
            throw new Error("Unauthorized");
          } else {
            throw new Error("Failed to fetch groups");
          }
        })
        .then((data) => {
          setGroups(data);
          setLoading(false);
        })
        .catch((err) => {
          console.error(err);
          setError(err.message);
          setLoading(false);
        });
    } else {
      router.push("/login");
    }
  }, [router]);

  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]);

  // When the groups are loaded, fetch the user details corresponding to the creator_id
  useEffect(() => {
    if (groups.length > 0) {
      const creatorIds = groups.map((group: GroupData) => group.creator_id);
      // /api/users with JSON body { "user_ids": ["id1", "id2", ...] }
      fetch("/api/user-details", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify({ user_ids: creatorIds }),
      })
        .then((response) => {
          if (response.ok) return response.json();
          else throw new Error("Failed to fetch user details");
        })
        .then((data) => {
          const mapping: UserIdMapping = {};
          data.forEach((user: UserData) => {
            mapping[user.user_id] = user;
          });
          setUserIdMapping(mapping);
          console.log("Got user details:", data);
        })
        .catch((err) => {
          console.error(err);
        });
    }
  }, [groups]);

  const handleCardClick = (groupId: string) => {
    router.push(`/groups/${groupId}`);
  };

  const handleCreateGroup = () => {
    setCreatingGroup(true);
    setCreateError("");
    const accessToken = localStorage.getItem("access_token");

    if (!newGroupName.trim()) {
      setCreateError("Group name cannot be empty");
      setCreatingGroup(false);
      return;
    }

    if (accessToken) {
      fetch("/api/groups", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ group_name: newGroupName }),
      })
        .then((response) => {
          if (response.ok) return response.json();
          else if (response.status === 400) {
            throw new Error("Invalid group name");
          } else if (response.status === 401 || response.status === 403) {
            throw new Error("Unauthorized");
          } else {
            throw new Error("Failed to create group");
          }
        })
        .then((data) => {
          setOpenDialog(false);
          setNewGroupName("");
          setCreatingGroup(false);
          console.log("Created group:", data);
          // Re-fetch the groups list
          fetchGroups();
        })
        .catch((err) => {
          console.error(err);
          setCreateError(err.message);
          setCreatingGroup(false);
        });
    } else {
      router.push("/login");
    }
  };

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Dashboard
          </Typography>
          <Button color="inherit" onClick={() => setOpenDialog(true)}>
            Create Group
          </Button>
          <LogoutButton />
        </Toolbar>
      </AppBar>

      <Container maxWidth="md">
        <Box sx={{ mt: 4 }}>
          {loading ? (
            <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
              <CircularProgress />
            </Box>
          ) : error ? (
            <Typography color="error" variant="body1">
              {error}
            </Typography>
          ) : groups.length > 0 ? (
            <Grid2 container spacing={2}>
              {groups.map((group: GroupData) => (
                <Grid2 key={group.group_id}>
                  <Card>
                    <CardActionArea
                      onClick={() => handleCardClick(group.group_id)}
                    >
                      <CardContent>
                        <Typography variant="h5" component="div">
                          {group.group_name}
                        </Typography>
                        {/* Add more group details here I need it */}

                        {/* Only show the created by, if the userIdMapping is populated */}
                        {userIdMapping[group.creator_id] && (
                          <Typography variant="body2" color="textSecondary">
                            Created by{" "}
                            {userIdMapping[group.creator_id].username}
                          </Typography>
                        )}

                      </CardContent>
                    </CardActionArea>
                  </Card>
                </Grid2>
              ))}
            </Grid2>
          ) : (
            <Typography variant="body1">
              You are not subscribed to any groups.
            </Typography>
          )}
        </Box>

        {/* Group Creation Dialog */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
          <DialogTitle>Create New Group</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              id="group_name"
              label="Group Name"
              type="text"
              fullWidth
              variant="standard"
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
            />
            {createError && (
              <Typography color="error" variant="body2" sx={{ mt: 1 }}>
                {createError}
              </Typography>
            )}
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => setOpenDialog(false)}
              disabled={creatingGroup}
            >
              Cancel
            </Button>
            <Button onClick={handleCreateGroup} disabled={creatingGroup}>
              {creatingGroup ? "Creating..." : "Create"}
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </>
  );
}
